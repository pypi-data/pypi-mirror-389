"""

Configuration management module

"""

from .schema import (
    DataType,
    ResourceType,
    ConfigMetadata,
    ResourceConfig,
    ScraperConfig,
)

from .manager import ConfigManager

from .proxy_schema import ProxyConfig, ProxyList

from .proxy_manager import ProxyManager


__all__ = [
    "DataType",
    "ResourceType",
    "ConfigMetadata",
    "ResourceConfig",
    "ScraperConfig",
    "ConfigManager",
    "ProxyConfig",
    "ProxyList",
    "ProxyManager",
]
