"""

ScrapAI - AI-powered web scraping SDK

"""



from .scrapai_client import ScrapAIClient

from .config import ConfigManager, ScraperConfig, DataType, ResourceType

from .ai_tools import ConfigRunner, URLTester, ResponseValidator



__version__ = "0.5.0"


__all__ = [

    "ScrapAIClient",

    "ConfigManager",

    "ScraperConfig",

    "DataType",

    "ResourceType",

    "ConfigRunner",

    "URLTester",

    "ResponseValidator"

]
