"""
Proxy Configuration Schema using Pydantic

Defines proxy models with validation for HTTP, HTTPS, SOCKS proxies
and CDP connection configurations.
"""

from typing import Optional, Literal, List
from pydantic import BaseModel, Field, field_validator


class ProxyConfig(BaseModel):
    """
    Single proxy configuration with validation.

    Supports multiple proxy types:
    - HTTP/HTTPS proxies
    - SOCKS4/SOCKS5 proxies
    - CDP (Chrome DevTools Protocol) connections
    """

    # Identification
    name: str = Field(..., description="Unique name for this proxy")

    # Proxy Type
    proxy_type: Literal["http", "https", "socks4", "socks5", "cdp"] = Field(
        default="http", description="Type of proxy/connection"
    )

    # Connection Details
    host: str = Field(..., description="Proxy host or CDP endpoint")
    port: int = Field(..., ge=1, le=65535, description="Proxy port (1-65535)")

    # Authentication (optional)
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")

    # CDP-specific fields
    cdp_url: Optional[str] = Field(None, description="CDP WebSocket URL (for CDP type)")
    browser_type: Optional[Literal["chromium", "firefox", "webkit"]] = Field(
        None, description="Browser type for CDP connection"
    )

    # Metadata
    is_active: bool = Field(default=True, description="Whether proxy is active")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    description: Optional[str] = Field(None, description="Description of proxy")

    # Validation & Status
    last_validated: Optional[str] = Field(None, description="Last validation timestamp")
    is_valid: bool = Field(default=False, description="Whether proxy passed validation")
    validation_error: Optional[str] = Field(
        None, description="Last validation error message"
    )

    # Usage stats
    success_count: int = Field(default=0, description="Successful requests count")
    failure_count: int = Field(default=0, description="Failed requests count")

    # Timestamps
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host format."""
        if not v or not v.strip():
            raise ValueError("Host cannot be empty")
        # Remove protocol if present
        v = (
            v.replace("http://", "")
            .replace("https://", "")
            .replace("ws://", "")
            .replace("wss://", "")
        )
        # Remove trailing slash
        v = v.rstrip("/")
        return v.strip()

    @field_validator("cdp_url")
    @classmethod
    def validate_cdp_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate CDP URL format."""
        if v is None:
            return v

        if not v.startswith(("ws://", "wss://")):
            raise ValueError("CDP URL must start with ws:// or wss://")

        return v

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(exclude_none=True)

    def to_requests_format(self) -> dict:
        """
        Convert to requests library format.

        Returns:
            Dict with 'http' and 'https' keys for requests library
        """
        if self.proxy_type == "cdp":
            raise ValueError("CDP proxies cannot be converted to requests format")

        auth_str = ""
        if self.username and self.password:
            auth_str = f"{self.username}:{self.password}@"

        proxy_url = f"{self.proxy_type}://{auth_str}{self.host}:{self.port}"

        return {"http": proxy_url, "https": proxy_url}

    def to_playwright_format(self) -> dict:
        """
        Convert to Playwright proxy format.

        Returns:
            Dict with proxy configuration for Playwright
        """
        if self.proxy_type == "cdp":
            return {
                "cdp_url": self.cdp_url,
                "browser_type": self.browser_type or "chromium",
            }

        result = {"server": f"{self.proxy_type}://{self.host}:{self.port}"}

        if self.username and self.password:
            result["username"] = self.username
            result["password"] = self.password

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "ProxyConfig":
        """Create ProxyConfig from dictionary."""
        return cls(**data)


class ProxyList(BaseModel):
    """
    Collection of proxy configurations.

    Stores multiple proxies with metadata.
    """

    proxies: List[ProxyConfig] = Field(
        default_factory=list, description="List of proxies"
    )
    version: str = Field(default="1.0", description="Schema version")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "proxies": [proxy.to_dict() for proxy in self.proxies],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProxyList":
        """Create ProxyList from dictionary."""
        proxies = [ProxyConfig.from_dict(p) for p in data.get("proxies", [])]
        return cls(
            proxies=proxies,
            version=data.get("version", "1.0"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
