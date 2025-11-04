"""

Scraping Agent - Interactive AI agent with tools

"""
import asyncio
import json

import inspect

from typing import Dict, List, Any, Optional

from datetime import datetime

from pathlib import Path

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .system_prompt import SystemPrompt

from .xml_parser import XMLConfigParser
from ..ai_tools.tools import AgentTools

from ..config.manager import ConfigManager

from ..ai_services.config import AIServiceConfig

from ..utils.browser_client import BrowserClient

from ..ai_analyzer.api_finder import APIFinder

from ..ai_agent.agent import Agent

class IntelligentAnalyzer:

    """

    Interactive AI agent for creating scraping configurations.

    Uses tools to analyze URLs, create configs, test and validate results.

    """

    def __init__(

        self,

        config_manager: ConfigManager,

        service_config: AIServiceConfig,

        proxies: Optional[Dict] = None,

        max_context_messages: int = 25,

        enable_logging: bool = True,

        raise_exceptions: bool = True

    ):

        """

        Initialize intelligent analyzer.

        Args:

            config_manager: ConfigManager instance

            service_config: AIServiceConfig with service name, key, base_url, model

            proxies: Optional proxy configuration

            max_context_messages: Max messages to keep in context (default: 25)

            enable_logging: Enable/disable logging

            raise_exceptions: Raise exceptions or handle gracefully

        """

        self.enable_logging = enable_logging

        self.raise_exceptions = raise_exceptions

        self.config_manager = config_manager

        self.tools = AgentTools(config_manager, proxies, enable_logging=enable_logging)

        self.service_config = service_config

        # Initialize Agent for conversation history and model calls
        self.agent = Agent(
            service_config=service_config,
            max_context_messages=max_context_messages,
            enable_logging=enable_logging
        )

        # XML parser (handles validation, syntax, and parsing)
        self.xml_parser = XMLConfigParser()

        # System prompt (for building initial messages)
        self.system_prompt = SystemPrompt.get_system_prompt()

    def _log(self, level: str, message: str):

        """

        Centralized logging method.

        Args:

            level: Log level (INFO, DEBUG, WARNING, ERROR)

            message: Log message

        """

        if self.enable_logging:

            prefix = f"[{level}]" if level else ""

            print(f"{prefix} {message}")

    def _get_available_actions_prompt(self) -> str:

        """Get formatted available actions for prompt."""

        return self.tools.get_available_actions_formatted()

    def _get_available_configs_prompt(self) -> str:

        """Get formatted available configs for prompt."""

        config_names = self.tools.list_configs()

        return SystemPrompt.format_available_configs(config_names)

    def _build_initial_user_message(self, url: str, description: str) -> str:  # noqa: C0301

        """

        Build initial user message with all context and pre-processed data.

        Args:

            url: Target URL

            description: Description of what to scrape

            pre_analysis: Optional pre-processed analysis results

        Returns:

            User prompt with actions, configs, and pre-analysis

        """

        actions = self._get_available_actions_prompt()

        configs = self._get_available_configs_prompt()

        base_message = SystemPrompt.build_user_prompt(url, description, actions, configs)

        # Add pre-processed analysis in XML format
        pre_analysis = asyncio.run(self.tools.fetch_url_content(url))
        base_message += f"\n\n## Here is Auto fetched URL-content \n```{pre_analysis}```, Please analize this and find the best configuration for crawler and call tools if requried"

        return base_message

    async def create_config_interactive(

        self,

        url: str,

        description: str,

        target_config: Optional[str] = None,

        max_iterations: int = 5

    ) -> Dict[str, Any]:

        """

        Interactively create a scraping configuration using AI agent.

        Args:

            url: Target URL to scrape

            description: Description of what to scrape

            target_config: Optional existing config name to add to (e.g., "pow_config")

            max_iterations: Max agent iterations

        Returns:

            Dict with config, conversation log, and status

        """

        result = {

            "success": False,

            "config": None,

            "config_name": target_config,

            "mode": "create" if not target_config else "add_to_existing",

            "iterations": 0,

            "error": None

        }

        # Check if target_config exists

        if target_config:

            existing = self.config_manager.load_config_dict(target_config)

            if not existing:

                result["error"] = f"Target config '{target_config}' not found. Will create new config."

                result["mode"] = "create"

                result["config_name"] = None

                self._log("WARNING", f"Target config '{target_config}' not found, will create new")

        # PRE-PROCESSING: Analyze URL before first AI call

        self._log("INFO", "Starting pre-processing: Fetching and analyzing URL...")

        user_message = self._build_initial_user_message(url, description)

        # Add target config info if specified

        if target_config and result["mode"] == "add_to_existing":

            user_message += f"\n\n**IMPORTANT**: User wants to ADD this to existing config: '{target_config}'. Read the existing config first to learn its structure and patterns."  # noqa: C0301

        self.agent.system_prompt = {"role":"system", "content": self.system_prompt}
        # Agent loop
        for iteration in range(max_iterations):
            result["iterations"] = iteration + 1

            self._log("INFO", f"\n{'='*60}")
            self._log("INFO", f"Iteration {iteration + 1}/{max_iterations}")
            self._log("INFO", f"{'='*60}")

            try:

                self._log("DEBUG", f"Sending request to AI ({self.service_config.service_name}/{self.service_config.get_model()})...")
                self._log("DEBUG", f"Subsequent call: user message ({len(user_message)} chars)")
                ai_message = self.agent.call_model({"role": "user", "content": user_message})

                self._log("DEBUG", f"Response received ({len(ai_message)} chars)")

                # Validate and parse XML response
                validation_result = self.xml_parser.validate_and_parse(ai_message)

                if not validation_result["valid"]:
                    # Invalid XML - prepare error feedback for next iteration
                    self._log("WARNING", f"Invalid XML response: {validation_result['error']}")
                    self._log("DEBUG", f"Response preview: {ai_message[:500]}...")

                    error_feedback = self.xml_parser.create_error_feedback(validation_result)

                    # Set pending message for next iteration
                    user_message = error_feedback
                    continue

                # Now use the parsed validation_result directly

                done_detected = validation_result["done"]

                tool_calls_from_xml = validation_result["tool_calls"]

                configs_xml_list = validation_result["configs"]

                message_content = validation_result.get("message")

                if message_content:

                    self._log("DEBUG", f"AI message: {message_content[:200]}...")

                if done_detected:

                    self._log("INFO", "\n✓ AI signaled completion (<status>DONE</status> found in XML response)")

                    if configs_xml_list:

                        self._log("DEBUG", f"Found {len(configs_xml_list)} config(s) in response")

                        for idx, config_xml in enumerate(configs_xml_list):

                            self._log("DEBUG", f"Config {idx+1} preview: {config_xml[:200]}...")

                    else:

                        self._log("WARNING", "No configs found in DONE response")

                    if configs_xml_list:

                        # Parse all configs from XML

                        self._log("DEBUG", "Parsing XML configs...")

                        configs_list = []

                        try:

                            for config_xml in configs_xml_list:

                                parsed = self.xml_parser.parse_configs_xml(config_xml)

                                configs_list.extend(parsed)

                            self._log("INFO", f"Parsed {len(configs_list)} config(s) from XML")

                        except Exception as e:

                            self._log("ERROR", f"XML parsing failed: {e}")

                            configs_list = []

                    else:

                        configs_list = []

                        self._log("ERROR", "No config XML found in response")

                    if configs_list:

                        # If multiple configs, save all of them

                        if len(configs_list) > 1:

                            self._log("INFO", f"Found {len(configs_list)} configs, saving all...")

                            saved_configs = []

                            for idx, config_dict in enumerate(configs_list):

                                extracted_name = config_dict.get("config_name") or f"config_{idx+1}"

                                if self.config_manager.save_config_dict(extracted_name, config_dict):

                                    saved_configs.append(extracted_name)

                            if saved_configs:

                                result["success"] = True

                                result["config"] = configs_list[0]

                                result["config_name"] = saved_configs[0]

                                self._log("INFO", f"✓ Saved {len(saved_configs)} config(s): {saved_configs}")

                                break

                        else:

                            # Single config

                            config_dict = configs_list[0]

                            entities = config_dict.get("entities", {})

                            self._log("DEBUG", f"Config validation - Name: {config_dict.get('config_name', 'N/A')}, Entities: {len(entities)}")  # noqa: C0301

                            if not entities or len(entities) == 0:

                                error_msg = "Generated config has no entities. Config must contain at least one entity with metrics."  # noqa: C0301

                                self._log("ERROR", f"VALIDATION FAILED: {error_msg}")

                                error_user_message = f"Error: {error_msg}. Please generate a valid config with entities and metrics."  # noqa: C0301

                                # Set pending message for next iteration
                                user_message = error_user_message
                                continue

                            extracted_name = config_dict.get("config_name") or "unnamed_config"

                            if extracted_name == "unnamed_config":

                                if target_config:

                                    extracted_name = target_config

                                else:

                                    if entities:

                                        first_entity = list(entities.keys())[0]

                                        extracted_name = f"{first_entity}_config"

                                    else:

                                        extracted_name = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                            self._log("INFO", f"✓ Config '{extracted_name}' created successfully with {len(entities)} entity/entities")  # noqa: C0301

                            result["success"] = True

                            result["config"] = config_dict

                            result["config_name"] = extracted_name

                            break

                # Use tool calls from parsed XML

                if tool_calls_from_xml:

                    self._log("INFO", f"Found {len(tool_calls_from_xml)} tool call(s) in AI response")

                    tool_results = []

                    for idx, tool_call in enumerate(tool_calls_from_xml, 1):

                        tool_name = tool_call['tool_name']  # Note: XMLConfigParser uses 'tool_name' not 'name'

                        tool_args = tool_call.get("args", {})

                        self._log("DEBUG", f"[Tool {idx}/{len(tool_calls_from_xml)}] Calling: {tool_name}")

                        if tool_args:

                            self._log("DEBUG", f"Arguments: {json.dumps(tool_args, indent=2)[:500]}...")

                        try:

                            tool_result = await self.tools.execute_tool(tool_name, tool_args)

                            if isinstance(tool_result, dict) and "error" in tool_result:

                                self._log("ERROR", f"Tool error: {tool_result.get('error')}")

                            elif isinstance(tool_result, dict) and "success" in tool_result:

                                success = tool_result.get("success", False)

                                status = "✓ Success" if success else "✗ Failed"

                                self._log("INFO", f"[Tool] {status}")

                            else:

                                result_str = str(tool_result)[:300]

                                self._log("DEBUG", f"Tool result: {result_str}...")

                            tool_results.append({

                                "tool": tool_name,

                                "result": tool_result

                            })

                        except Exception as e:

                            error_msg = f"Tool execution error: {str(e)}"

                            self._log("ERROR", f"Tool exception: {error_msg}")

                            tool_results.append({

                                "tool": tool_name,

                                "result": {"error": error_msg}

                            })

                    # Build tool results message for conversation

                    tool_message = "Tool Results:\n"

                    for tr in tool_results:

                        result_str = json.dumps(tr['result'], indent=2)

                        tool_message += f"\n{tr['tool']}: {result_str}\n"

                    self._log("DEBUG", f"Adding tool results to conversation context ({len(tool_message)} chars)")

                    # Set pending message for next iteration (agent will add to history and call model)
                    user_message = tool_message

                    # Continue to next iteration which will call agent with tool_message

                else:

                    # No tool calls, might be asking for clarification

                    # In production, this would wait for user input

                    # For now, we'll just continue

                    pass

            except Exception as e:

                self._log("ERROR", f"Error in iteration {iteration + 1}: {str(e)}")

                if self.raise_exceptions:

                    result["error"] = str(e)

                    break

                else:

                    # Continue to next iteration

                    continue

        if not result["success"] and not result["error"]:

            result["error"] = f"Max iterations ({max_iterations}) reached without completion"

            self._log("WARNING", result["error"])

        return result

    # Old XML parsing methods removed - now using XMLConfigParser class

    def test_config(self, config_name: str) -> Dict[str, Any]:

        """

        Test an existing configuration with AI validation.

        Args:

            config_name: Name of config to test

        Returns:

            Test results with AI validation

        """

        # Load config

        config = self.config_manager.load_config_dict(config_name)

        if not config:

            return {"error": f"Config '{config_name}' not found"}

        # Execute config (would use ExecutionEngine in production)

        test_result = {"note": "Test execution not yet integrated"}

        # Ask AI to validate

        validation_message = """

Please validate these results for config '{config_name}':

Config: {json.dumps(config, indent=2)}

Results: {json.dumps(test_result, indent=2)}

Are these results correct? If not, what needs to be fixed?

"""

        # Build messages for agent (first call - include system prompt)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": validation_message}
        ]
        
        try:
            # Call agent (first call - list format)
            validation = self.agent.call_model(messages)

            return {

                "config_name": config_name,

                "test_result": test_result,

                "ai_validation": validation

            }

        except Exception as e:

            return {"error": str(e)}

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get current conversation history from agent."""
        return self.agent.get_conversation_history()

    def clear_conversation_history(self):
        """Clear conversation history in agent."""
        self.agent.clear_conversation_history()
