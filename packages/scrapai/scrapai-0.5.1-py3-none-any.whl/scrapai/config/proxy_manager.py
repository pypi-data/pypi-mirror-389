"""
Proxy Manager - Manage proxy configurations with validation

Handles CRUD operations for proxies, validation, and CDP connections.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

import requests
from playwright.async_api import async_playwright

from .proxy_schema import ProxyConfig, ProxyList

logger = logging.getLogger(__name__)


class ProxyManager:
    """Manage proxy configurations with validation"""

    def __init__(self, base_path: str = "."):
        """
        Initialize proxy manager.

        Args:
            base_path: Base directory containing .scrapai folder
        """
        self.base_path = Path(base_path)
        self.scrapai_dir = self.base_path / ".scrapai"
        self.proxies_file = self.scrapai_dir / "proxies.json"

        # Ensure directory exists
        self.scrapai_dir.mkdir(parents=True, exist_ok=True)

        # Load existing proxies
        self._proxy_list: Optional[ProxyList] = self._load_proxies()

    def _load_proxies(self) -> Optional[ProxyList]:
        """Load proxies from file."""
        if not self.proxies_file.exists():
            return ProxyList(proxies=[])

        try:
            with open(self.proxies_file, "r") as f:
                data = json.load(f)
                return ProxyList.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load proxies: {e}")
            return ProxyList(proxies=[])

    def _save_proxies(self) -> bool:
        """Save proxies to file."""
        try:
            if self._proxy_list is None:
                self._proxy_list = ProxyList(proxies=[])

            # Update timestamps
            if not self._proxy_list.created_at:
                self._proxy_list.created_at = datetime.utcnow().isoformat()
            self._proxy_list.updated_at = datetime.utcnow().isoformat()

            with open(self.proxies_file, "w") as f:
                json.dump(self._proxy_list.to_dict(), f, indent=2)

            logger.info(f"Proxies saved to {self.proxies_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save proxies: {e}")
            return False

    def add_proxy(
        self,
        name: str,
        host: str,
        port: int,
        proxy_type: str = "http",
        username: Optional[str] = None,
        password: Optional[str] = None,
        cdp_url: Optional[str] = None,
        browser_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> ProxyConfig:
        """
        Add a new proxy configuration.

        Args:
            name: Unique proxy name
            host: Proxy host
            port: Proxy port
            proxy_type: Type (http, https, socks4, socks5, cdp)
            username: Optional username
            password: Optional password
            cdp_url: CDP WebSocket URL (for CDP type)
            browser_type: Browser type (for CDP)
            tags: Optional tags
            description: Optional description
            is_active: Whether proxy is active

        Returns:
            Created ProxyConfig

        Raises:
            ValueError: If proxy with same name exists or validation fails
        """
        if self._proxy_list is None:
            self._proxy_list = ProxyList(proxies=[])

        # Check if name already exists
        if any(p.name == name for p in self._proxy_list.proxies):
            raise ValueError(f"Proxy with name '{name}' already exists")

        # Create proxy config
        proxy = ProxyConfig(
            name=name,
            host=host,
            port=port,
            proxy_type=proxy_type,
            username=username,
            password=password,
            cdp_url=cdp_url,
            browser_type=browser_type,
            tags=tags or [],
            description=description,
            is_active=is_active,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )

        # Add to list
        self._proxy_list.proxies.append(proxy)

        # Save
        self._save_proxies()

        logger.info(f"Added proxy: {name}")
        return proxy

    def get_proxy(self, name: str) -> Optional[ProxyConfig]:
        """Get proxy by name."""
        if self._proxy_list is None:
            return None

        for proxy in self._proxy_list.proxies:
            if proxy.name == name:
                return proxy
        return None

    def list_proxies(self, active_only: bool = False) -> List[ProxyConfig]:
        """
        List all proxies.

        Args:
            active_only: Only return active proxies

        Returns:
            List of ProxyConfig objects
        """
        if self._proxy_list is None:
            return []

        proxies = self._proxy_list.proxies
        if active_only:
            proxies = [p for p in proxies if p.is_active]

        return proxies

    def update_proxy(self, name: str, **kwargs) -> Optional[ProxyConfig]:
        """
        Update proxy configuration.

        Args:
            name: Proxy name
            **kwargs: Fields to update

        Returns:
            Updated ProxyConfig or None if not found
        """
        proxy = self.get_proxy(name)
        if not proxy:
            return None

        # Update fields
        for key, value in kwargs.items():
            if hasattr(proxy, key):
                setattr(proxy, key, value)

        proxy.updated_at = datetime.utcnow().isoformat()

        # Save
        self._save_proxies()

        logger.info(f"Updated proxy: {name}")
        return proxy

    def remove_proxy(self, name: str) -> bool:
        """
        Remove proxy by name.

        Args:
            name: Proxy name

        Returns:
            True if removed, False if not found
        """
        if self._proxy_list is None:
            return False

        initial_count = len(self._proxy_list.proxies)
        self._proxy_list.proxies = [
            p for p in self._proxy_list.proxies if p.name != name
        ]

        if len(self._proxy_list.proxies) < initial_count:
            self._save_proxies()
            logger.info(f"Removed proxy: {name}")
            return True

        return False

    async def validate_proxy(
        self, name: str, test_url: str = "https://httpbin.org/ip"
    ) -> Dict[str, Any]:
        """
        Validate proxy connectivity and functionality.

        Args:
            name: Proxy name
            test_url: URL to test against

        Returns:
            Dict with validation results
        """
        proxy = self.get_proxy(name)
        if not proxy:
            return {"success": False, "error": f"Proxy '{name}' not found"}

        result = {
            "proxy_name": name,
            "success": False,
            "is_valid": False,
            "error": None,
            "response_time_ms": None,
            "test_url": test_url,
        }

        try:
            if proxy.proxy_type == "cdp":
                # Validate CDP connection
                cdp_result = await self._validate_cdp_connection(proxy, test_url)
                result.update(cdp_result)
            else:
                # Validate HTTP proxy
                http_result = await self._validate_http_proxy(proxy, test_url)
                result.update(http_result)

            # Update proxy status
            proxy.is_valid = result["is_valid"]
            proxy.last_validated = datetime.utcnow().isoformat()
            proxy.validation_error = result.get("error")

            if result["is_valid"]:
                proxy.success_count += 1
            else:
                proxy.failure_count += 1

            self._save_proxies()

        except Exception as e:
            result["error"] = str(e)
            proxy.is_valid = False
            proxy.last_validated = datetime.utcnow().isoformat()
            proxy.validation_error = str(e)
            proxy.failure_count += 1
            self._save_proxies()

        return result

    async def _validate_http_proxy(
        self, proxy: ProxyConfig, test_url: str
    ) -> Dict[str, Any]:
        """Validate HTTP/HTTPS/SOCKS proxy."""
        import time

        result = {
            "success": False,
            "is_valid": False,
            "error": None,
            "response_time_ms": None,
        }

        try:
            # Convert to requests format
            proxy_dict = proxy.to_requests_format()

            # Test connection
            start_time = time.time()
            response = requests.get(
                test_url, proxies=proxy_dict, timeout=10, verify=False
            )
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result["success"] = True
                result["is_valid"] = True
                result["response_time_ms"] = round(response_time, 2)
            else:
                result["error"] = f"HTTP {response.status_code}"

        except requests.exceptions.ProxyError as e:
            result["error"] = f"Proxy connection failed: {e}"
        except requests.exceptions.Timeout:
            result["error"] = "Connection timeout"
        except Exception as e:
            result["error"] = f"Validation error: {e}"

        return result

    async def _validate_cdp_connection(
        self, proxy: ProxyConfig, test_url: str = "https://httpbin.org/html"
    ) -> Dict[str, Any]:
        """
        Validate CDP connection.

        Args:
            proxy: ProxyConfig with CDP settings
            test_url: Test URL to navigate to (default: httpbin.org/html)
        """
        result = {
            "success": False,
            "is_valid": False,
            "error": None,
            "response_time_ms": None,
        }

        if not proxy.cdp_url:
            result["error"] = "CDP URL not specified"
            return result

        try:
            import time

            start_time = time.time()

            # Try to connect via Playwright
            async with async_playwright() as p:
                browser = await p.chromium.connect_over_cdp(proxy.cdp_url)

                # Create a test page
                context = await browser.new_context()
                page = await context.new_page()

                # Try to navigate to a real test URL (not data: URL)
                await page.goto(test_url, timeout=10000, wait_until="domcontentloaded")

                # Verify page loaded
                content = await page.content()
                if not content or len(content) < 100:
                    raise ValueError("Page content too short or empty")

                # Close
                await page.close()
                await context.close()
                await browser.close()

            response_time = (time.time() - start_time) * 1000

            result["success"] = True
            result["is_valid"] = True
            result["response_time_ms"] = round(response_time, 2)

        except Exception as e:
            result["error"] = f"CDP connection failed: {e}"

        return result

    def get_proxy_for_requests(self, name: Optional[str] = None) -> Dict[str, str]:
        """
        Get proxy in requests library format.

        Args:
            name: Proxy name (if None, returns first active proxy)

        Returns:
            Dict with 'http' and 'https' keys
        """
        if name:
            proxy = self.get_proxy(name)
        else:
            # Get first active proxy
            proxies = self.list_proxies(active_only=True)
            if not proxies:
                return {}
            proxy = proxies[0]

        if not proxy or proxy.proxy_type == "cdp":
            return {}

        return proxy.to_requests_format()

    def get_proxy_for_playwright(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get proxy in Playwright format.

        Args:
            name: Proxy name (if None, returns first active proxy)

        Returns:
            Dict with Playwright proxy config
        """
        if name:
            proxy = self.get_proxy(name)
        else:
            # Get first active proxy
            proxies = self.list_proxies(active_only=True)
            if not proxies:
                return {}
            proxy = proxies[0]

        if not proxy:
            return {}

        return proxy.to_playwright_format()
