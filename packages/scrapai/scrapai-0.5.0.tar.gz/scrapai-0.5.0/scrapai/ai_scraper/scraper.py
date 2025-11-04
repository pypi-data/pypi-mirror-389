"""
Intelligent Scraper - Direct data extraction without configuration files

Similar to ScrapeGraphAI's SmartScraper: extracts structured data on-demand.
"""
import asyncio
import json
from typing import Dict, List, Any, Optional

from ..config.manager import ConfigManager
from ..ai_services.config import AIServiceConfig
from ..ai_agent.agent import Agent
from ..ai_tools.tools import AgentTools
from .system_prompt import ScraperSystemPrompt
from .data_parser import DataParser


class IntelligentScraper:
    """
    Direct scraping using AI without creating config files.
    
    Extracts structured data from web pages based on natural language descriptions.
    Returns data immediately (real-time), doesn't save configurations.
    
    Example:
        scraper = IntelligentScraper(...)
        result = await scraper.smartscraper(
            url="https://etherscan.io/token/0xdac17f958d2ee523a2206206994597c13d831ec7",
            description="Get Max Total Supply, Holders, Price in ETH, Transfers in 24 hours and total"
        )
        # Returns: {"max_total_supply": "...", "holders": 123, ...}
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
        Initialize intelligent scraper.
        
        Args:
            config_manager: ConfigManager instance (for tool access)
            service_config: AIServiceConfig with service name, key, base_url, model
            proxies: Optional proxy configuration
            max_context_messages: Max messages to keep in context (default: 25)
            enable_logging: Enable/disable logging
            raise_exceptions: Raise exceptions or handle gracefully
        """
        self.enable_logging = enable_logging
        self.raise_exceptions = raise_exceptions
        self.config_manager = config_manager
        self.service_config = service_config
        
        # Initialize tools for content fetching
        self.tools = AgentTools(config_manager, proxies, enable_logging=enable_logging)
        
        # Initialize Agent for conversation history and model calls
        self.agent = Agent(
            service_config=service_config,
            max_context_messages=max_context_messages,
            enable_logging=enable_logging
        )
        
        # Data parser (handles XML responses with extracted data)
        self.data_parser = DataParser()
        
        # System prompt (for building initial messages)
        self.system_prompt = ScraperSystemPrompt.get_system_prompt()
    
    def _log(self, level: str, message: str):
        """Centralized logging method."""
        if self.enable_logging:
            prefix = f"[{level}]" if level else ""
            print(f"{prefix} {message}")
    
    def _build_user_message(self, url: str, description: str, content: Dict[str, Any]) -> str:
        """
        Build user message with URL, description, and pre-fetched content.
        
        Args:
            url: Target URL
            description: What data to extract
            content: Pre-fetched content from URL
            
        Returns:
            User prompt message
        """
        from bs4 import BeautifulSoup
        
        message = f"""Extract the following data from this webpage:

**URL**: {url}

**Description**: {description}

**Content**:
"""
        
        # Add content based on type
        if content.get("is_json"):
            # JSON content - send as-is
            content_str = json.dumps(content.get("content"), indent=2)
            message += f"```json\n{content_str}\n```"
        else:
            # HTML content - extract text using BeautifulSoup
            html_content = content.get("content", "")
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                # Extract all text content
                text_content = soup.get_text(separator='\n', strip=True)
                # Send clean text
                message += f"```\n{text_content}\n```"
            except Exception as e:
                # Fallback: send raw HTML if parsing fails
                self._log("WARNING", f"Failed to parse HTML: {e}")
                message += f"```html\n{html_content}\n```"
        
        message += "\n\n**Instructions**: Find and extract all requested fields from the content above. Return as JSON."
        
        return message
    
    async def smartscraper(
        self,
        url: str,
        description: str,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Extract structured data from a webpage using natural language description.
        
        Similar to ScrapeGraphAI's SmartScraper: takes URL and description,
        returns extracted data as JSON (not a configuration file).
        
        Args:
            url: Target URL to scrape
            description: Natural language description of what to extract
                Example: "Get Max Total Supply, Holders, Price in ETH, Transfers in 24 hours and total"
            max_iterations: Maximum AI iterations (default: 3)
            
        Returns:
            Dictionary with:
            {
                "success": bool,
                "data": Dict/List with extracted data (if success),
                "error": Optional[str],
                "iterations": int,
                "metadata": {
                    "url": str,
                    "description": str,
                    "execution_time": float
                }
            }
        """
        import time
        start_time = time.time()
        
        result = {
            "success": False,
            "data": None,
            "error": None,
            "iterations": 0,
            "metadata": {
                "url": url,
                "description": description,
                "execution_time": 0.0
            }
        }
        
        try:
            # Step 1: Pre-fetch content (like ScrapeGraphAI does)
            self._log("INFO", f"Pre-fetching content from {url}...")
            content_result = await self.tools.fetch_url_content(url, render_js=False, is_truncate=False)
            
            # Handle errors - if 403 occurred, browser rendering was already attempted
            if content_result.get("error"):
                error_msg = content_result['error']
                # If it's a 403 error, browser rendering was attempted but may have failed
                # Still try to continue with any partial content we might have
                if "403" in error_msg or "HTTP 403" in error_msg:
                    self._log("WARNING", f"HTTP 403 for {url} - browser rendering attempted, continuing with available content...")
                    # Continue - might have partial content or browser rendering succeeded
                    if not content_result.get("content"):
                        # No content at all, this is a real failure
                        result["error"] = f"Failed to fetch URL: {error_msg}"
                        if self.raise_exceptions:
                            raise ValueError(result["error"])
                        return result
                else:
                    # Other errors - fail immediately
                    result["error"] = f"Failed to fetch URL: {error_msg}"
                    if self.raise_exceptions:
                        raise ValueError(result["error"])
                    return result
            
            # Step 2: Build user message with content
            user_message = self._build_user_message(url, description, content_result)
            
            # Step 3: Set system prompt on agent
            self.agent.system_prompt = {"role": "system", "content": self.system_prompt}
            
            # Step 4: Agent loop
            for iteration in range(max_iterations):
                result["iterations"] = iteration + 1
                
                self._log("INFO", f"\n{'='*60}")
                self._log("INFO", f"Iteration {iteration + 1}/{max_iterations}")
                self._log("INFO", f"{'='*60}")
                
                try:
                    # Call AI model
                    if iteration == 0:
                        # First call: send system prompt + user message
                        ai_response = self.agent.call_model([
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": user_message}
                        ])
                    else:
                        # Subsequent calls: just user message
                        ai_response = self.agent.call_model({"role": "user", "content": user_message})
                    
                    self._log("DEBUG", f"AI response received ({len(ai_response)} chars)")
                    
                    # Parse XML response
                    parse_result = self.data_parser.parse_extracted_data(ai_response)
                    
                    if not parse_result["valid"]:
                        # Invalid XML - prepare error feedback
                        self._log("WARNING", f"Invalid XML response: {parse_result['error']}")
                        error_feedback = self.data_parser.create_error_feedback(
                            f"Invalid XML format: {parse_result['error']}. Please return valid XML with <extracted_data><data>JSON</data></extracted_data>"
                        )
                        user_message = error_feedback
                        continue
                    
                    # Check if done
                    if parse_result.get("done"):
                        self._log("INFO", "✓ AI signaled completion")
                        
                        # Extract data
                        if parse_result.get("data"):
                            result["success"] = True
                            result["data"] = parse_result["data"]
                            
                            if parse_result.get("message"):
                                self._log("INFO", f"AI message: {parse_result['message']}")
                            
                            # Success - break loop
                            break
                        else:
                            self._log("WARNING", "Done but no data extracted")
                            result["error"] = "AI returned done status but no data was extracted"
                            if self.raise_exceptions:
                                raise ValueError(result["error"])
                            return result
                    else:
                        # Still processing - continue
                        if parse_result.get("message"):
                            self._log("INFO", f"AI message: {parse_result['message']}")
                            # Use message as feedback for next iteration
                            user_message = f"Continue extraction: {parse_result['message']}"
                        continue
                
                except Exception as e:
                    error_msg = f"Error in iteration {iteration + 1}: {str(e)}"
                    self._log("ERROR", error_msg)
                    result["error"] = error_msg
                    
                    if self.raise_exceptions:
                        raise
                    return result
            
            # If we exhausted iterations
            if not result["success"]:
                result["error"] = f"Failed to extract data after {max_iterations} iterations"
                if self.raise_exceptions:
                    raise ValueError(result["error"])
            
            # Calculate execution time
            result["metadata"]["execution_time"] = time.time() - start_time
            
            return result
        
        except Exception as e:
            error_msg = f"Unexpected error in smartscraper: {str(e)}"
            self._log("ERROR", error_msg)
            result["error"] = error_msg
            result["metadata"]["execution_time"] = time.time() - start_time
            
            if self.raise_exceptions:
                raise
            return result

