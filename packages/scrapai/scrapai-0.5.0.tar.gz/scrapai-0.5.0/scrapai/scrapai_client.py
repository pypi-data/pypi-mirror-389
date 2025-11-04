"""
ScrapAI Client - Main SDK interface

Single entry point for all ScrapAI operations.
Manages configuration, AI services, and delegates to internal components.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from .config.manager import ConfigManager
from .crawler.execution_engine import ExecutionEngine
from .ai_tools import ConfigRunner, URLTester, ResponseValidator
from .ai_analyzer.analyzer import IntelligentAnalyzer
from .ai_scraper.scraper import IntelligentScraper
from .ai_services.config import AIServiceConfig
from .ai_services.registry import AIServiceRegistry
from .code_generator import CodeGenerator

logger = logging.getLogger(__name__)


class ScrapAIClient:
    """Main ScrapAI SDK client - Single entry point"""

    def __init__(
        self,
        proxies: Optional[Dict] = None,
        # Legacy OpenAI support (backward compatible)
        service_name: Optional[str] = None,
        service_key: Optional[str] = None,
        service_base_url: Optional[str] = None,
        service_model: Optional[str] = None,
        base_path: Optional[str] = None,
        enable_logging: bool = True,
        raise_exceptions: bool = True
    ):
        """
        Initialize ScrapAI client.

        Args:
            proxies: Proxy configuration dict
            # Legacy parameters (backward compatible)
            # New multi-service parameters
            service_name: AI service name (openai, ollama, grok, anthropic, etc.)
            service_base_url: Optional custom base URL (auto-detected if None)
            service_model: Optional model name (uses service default if None)
            base_path: Base path for .scrapai folder
            enable_logging: Enable/disable logging (default: True)
            raise_exceptions: Raise exceptions or handle gracefully (default: True)
        """
        self.enable_logging = enable_logging
        self.raise_exceptions = raise_exceptions

        # Configure logging
        if not enable_logging:
            logging.disable(logging.CRITICAL)
        else:
            logging.basicConfig(
                level=logging.INFO,
                format='[%(levelname)s] %(name)s: %(message)s'
            )

        # Setup paths
        if base_path is None:
            base_path = os.getcwd()
        self.base_path = Path(base_path)
        self.scrapai_dir = self.base_path / ".scrapai"

        # Initialize config manager
        self.config_manager = ConfigManager(str(self.base_path))

        # Load proxies
        self.proxies = self._load_proxies(proxies)

        # Determine AI service configuration
        self.service_config = None
        if service_name and service_key:
            # New multi-service support
            self.service_config = AIServiceConfig(
                service_name=service_name,
                api_key=service_key,
                base_url=service_base_url,
                model=service_model
            )
            self.service_config.enable_logging = enable_logging
        # Initialize AI Analyzer (creates configs)
        self.analyzer = None
        if self.service_config:
            self.analyzer = IntelligentAnalyzer(
                config_manager=self.config_manager,
                service_config=self.service_config,
                proxies=self.proxies,
                enable_logging=enable_logging,
                raise_exceptions=raise_exceptions
            )
        
        # Initialize AI Scraper (direct data extraction)
        self.scraper = None
        if self.service_config:
            self.scraper = IntelligentScraper(
                config_manager=self.config_manager,
                service_config=self.service_config,
                proxies=self.proxies,
                enable_logging=enable_logging,
                raise_exceptions=raise_exceptions
            )

        # Initialize execution engine
        self.execution_engine = ExecutionEngine(
            self.config_manager,
            proxies=self.proxies,
            browser=None,
            context=None
        )

        # Initialize AI tools
        self.config_runner = ConfigRunner(self.proxies, None, None)
        self.url_tester = URLTester(self.proxies)
        self.response_validator = ResponseValidator()

        if self.enable_logging:
            logger.info(f"ScrapAI client initialized at {self.scrapai_dir}")
            if self.service_config:
                logger.info(f"AI Service: {self.service_config.service_name} ({self.service_config.base_url})")

    @staticmethod
    def list_available_services() -> List[str]:
        """List all available AI services in registry."""
        return AIServiceRegistry.list_services()

    @staticmethod
    def get_service_info(service_name: str) -> Optional[Dict]:
        """Get information about a specific service."""
        return AIServiceRegistry.get_service_info(service_name)

    def _load_proxies(self, proxies: Optional[Any] = None) -> Dict:
        """Load proxy configuration."""
        if proxies is None:
            # Try to load from .scrapai/proxies.json
            proxies_file = self.scrapai_dir / "proxies.json"
            if proxies_file.exists():
                try:
                    with open(proxies_file, "r") as f:
                        proxies_data = json.load(f)
                        if isinstance(proxies_data, list) and proxies_data:
                            proxy = proxies_data[0]
                            return {
                                "http": f"http://{proxy.get('username', '')}:{proxy.get('password', '')}@{proxy.get('host', '')}",
                                "https": f"http://{proxy.get('username', '')}:{proxy.get('password', '')}@{proxy.get('host', '')}"
                            }
                except Exception as e:
                    logger.warning(f"Failed to load proxies: {e}")
        elif isinstance(proxies, dict):
            return proxies
        return {}

    # ===== Main API Methods =====

    def list_configs(self) -> List[str]:
        """List all available configuration names."""
        return self.config_manager.list_config_names()

    async def add_config(
        self,
        url: str,
        description: str,
        name: Optional[str] = None,
        target_config: Optional[str] = None,
        max_iterations: int = 5
    ) -> Dict:
        """
        Add a new scraping configuration using AI analysis.

        Args:
            url: Target URL
            description: What to extract
            name: Optional config name (used if target_config not specified)
            target_config: Optional existing config to add to
            max_iterations: Maximum iterations for AI agent

        Returns:
            Created config dict or agent result
        """
        if not self.analyzer:
            if self.raise_exceptions:
                raise ValueError(
                    "AI service required. Provide either:\n"
                    "  - service_name + service_key (new way)\n"
                    "  - ai_api_key (legacy way)\n"
                    f"Available services: {AIServiceRegistry.list_services()}"
                )
            else:
                if self.enable_logging:
                    logger.error(f"AI service required. Available services: {AIServiceRegistry.list_services()}")
                return {"error": "AI service required"}

        if self.enable_logging:
            mode = f"adding to '{target_config}'" if target_config else "creating new config"
            logger.info(f"AI analyzer {mode} for URL: {url}")

        # Use intelligent analyzer
        result = await self.analyzer.create_config_interactive(
            url,
            description,
            target_config,
            max_iterations=max_iterations
        )

        if result["success"] and result["config"]:
            config_name = result.get("config_name") or name or "unnamed_config"
            if not result.get("config_name"):
                result["config_name"] = config_name

            if self.config_manager.save_config_dict(config_name, result["config"]):
                if self.enable_logging:
                    logger.info(f"✓ Config '{config_name}' created successfully")
                return {
                    "config_name": config_name,
                    "config": result["config"],
                    "iterations": result.get("iterations", 0)
                }
            else:
                error_msg = f"Failed to save config '{config_name}'"
                if self.raise_exceptions:
                    raise RuntimeError(error_msg)
                else:
                    if self.enable_logging:
                        logger.error(error_msg)
                    return {"error": error_msg}
        else:
            error_msg = f"Analyzer failed to create config: {result.get('error', 'Unknown error')}"
            if self.raise_exceptions:
                raise RuntimeError(error_msg)
            else:
                if self.enable_logging:
                    logger.error(error_msg)
                return {"error": error_msg}

    async def smartscraper(
        self,
        url: str,
        description: str,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Extract structured data from a webpage directly (no config creation).
        
        Similar to ScrapeGraphAI's SmartScraper: takes URL and natural language
        description, returns extracted data as JSON immediately.
        
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
            
        Example:
            client = ScrapAIClient(service_name="ollama", service_key="...")
            result = await client.smartscraper(
                url="https://etherscan.io/token/0xdac17f958d2ee523a2206206994597c13d831ec7",
                description="Get Max Total Supply, Holders, Price in ETH, Transfers in 24 hours and total"
            )
            # Returns: {"success": True, "data": {"max_total_supply": "...", "holders": 123, ...}}
        """
        if not self.scraper:
            if self.raise_exceptions:
                raise ValueError(
                    "AI service required for smartscraper. Provide:\n"
                    "  - service_name + service_key\n"
                    f"Available services: {AIServiceRegistry.list_services()}"
                )
            else:
                if self.enable_logging:
                    logger.error(f"AI service required. Available services: {AIServiceRegistry.list_services()}")
                return {
                    "success": False,
                    "error": "AI service required",
                    "data": None,
                    "iterations": 0,
                    "metadata": {"url": url, "description": description, "execution_time": 0.0}
                }
        
        if self.enable_logging:
            logger.info(f"AI scraper extracting data from: {url}")
        
        # Use intelligent scraper
        result = await self.scraper.smartscraper(
            url,
            description,
            max_iterations=max_iterations
        )
        
        if self.enable_logging:
            if result.get("success"):
                logger.info(f"✓ Data extracted successfully in {result['metadata'].get('execution_time', 0):.2f}s")
            else:
                logger.warning(f"✗ Data extraction failed: {result.get('error')}")
        
        return result

    def remove_config(self, name: str) -> bool:
        """Remove a configuration."""
        return self.config_manager.remove_config(name)

    async def execute_config(
        self,
        name: str,
        custom_utils_module=None
    ) -> Dict[str, Any]:
        """
        Execute a single configuration.

        Args:
            name: Config name
            custom_utils_module: Optional custom utils

        Returns:
            Execution result dict
        """
        if self.enable_logging:
            logger.info(f"Executing config: {name}")

        result = await self.execution_engine.execute_single_config(name, custom_utils_module)

        if self.enable_logging:
            if result.get("success"):
                logger.info(f"✓ Config '{name}' executed: {result['successful_metrics']}/{result['total_metrics']} metrics")
            else:
                logger.warning(f"✗ Config '{name}' execution had issues: {result.get('failed_metrics', 0)} failed")

        return result

    async def execute_all_configs(
        self,
        custom_utils_module=None,
        parallel: bool = True
    ) -> Dict[str, Dict]:
        """Execute all configurations."""
        return await self.execution_engine.execute_all_configs(
            custom_utils_module,
            parallel
        )

    def get_generated_code(self, name: str) -> str:
        """Get Python code for executing a configuration."""
        if not self.config_manager.config_exists(name):
            return f"# Config '{name}' not found"

        config = self.config_manager.load_config_object(name)
        if not config:
            return f"# Failed to load config '{name}'"

        generator = CodeGenerator(self.config_manager)
        return generator.generate_code(name)

    # ===== AI Tools Methods =====

    def test_url(self, url: str) -> Dict:
        """Test URL accessibility and analyze type."""
        accessibility = self.url_tester.test_url_accessibility(url)
        if accessibility["is_accessible"]:
            analysis = self.url_tester.analyze_url_type(url)
            accessibility.update(analysis)
        return accessibility

    async def run_config_test(self, name: str) -> Dict:
        """Run a test execution of a configuration."""
        config = self.config_manager.load_config_object(name)
        if not config:
            return {"error": "Config not found"}
        return await self.config_runner.run_config(config)

    async def dry_run_config(self, name: str) -> Dict:
        """Validate configuration without executing."""
        config = self.config_manager.load_config_object(name)
        if not config:
            return {"error": "Config not found"}
        return await self.config_runner.dry_run_config(config)

    def test_config_with_agent(self, name: str) -> Dict:
        """Test configuration and get AI validation."""
        if not self.analyzer:
            raise ValueError("AI analyzer not initialized (AI service required)")
        return self.analyzer.test_config(name)

    def get_agent_conversation(self) -> List[Dict]:
        """Get current agent conversation history."""
        if not self.analyzer:
            return []
        return self.analyzer.get_conversation_history()

    def clear_agent_conversation(self):
        """Clear agent conversation history."""
        if self.analyzer:
            self.analyzer.clear_conversation_history()

    async def close(self):
        """Clean up resources."""
        logger.info("ScrapAI client closed")
