"""

ScrapAI - AI-powered web scraping SDK

"""

from .scrapai_client import ScrapAIClient

from .config import ConfigManager, ScraperConfig, DataType, ResourceType
from .config.proxy_manager import ProxyManager
from .config.proxy_schema import ProxyConfig

from .ai_tools import ConfigRunner, URLTester, ResponseValidator



__version__ = "0.6.0"


__all__ = [
    "ScrapAIClient",
    "ConfigManager",
    "ScraperConfig",
    "DataType",
    "ResourceType",
    "ProxyManager",
    "ProxyConfig",
    "ConfigRunner",
    "URLTester",
    "ResponseValidator",
]
