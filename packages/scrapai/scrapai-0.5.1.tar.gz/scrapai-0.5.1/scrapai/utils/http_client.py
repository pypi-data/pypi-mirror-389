"""

HTTP Client - Properly named methods for API and web requests

"""

import requests

import time

import asyncio

import logging

import urllib3

from typing import Dict, Any, Optional
import random

from urllib.parse import urlparse

from fake_useragent import UserAgent


from .browser_client import BrowserClient


# Suppress SSL warnings when verify=False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client for API requests and HTML fetching with smart rendering"""

    def __init__(self, proxies: Optional[Dict] = None, proxy_manager=None):
        """

        Initialize HTTP client.



        Args:

            proxies: Proxy configuration dict (legacy, for backward compatibility)

            proxy_manager: ProxyManager instance for smart proxy handling

        """

        self.proxies = proxies or {}

        self.proxy_manager = proxy_manager

        self.user_agent = UserAgent()

        self.browser_client = BrowserClient(headless=True)

        self._user_agent_index = 0

    def _get_browser_headers(
        self, url: str, referer: Optional[str] = None
    ) -> Dict[str, str]:
        """

        Generate browser-like headers to mimic real browser requests.



        Args:

            url: Target URL

            referer: Optional referer URL



        Returns:

            Dict of browser headers

        """

        # Rotate user agent

        ua = self.user_agent.random

        # Parse URL for origin

        parsed = urlparse(url)

        origin = f"{parsed.scheme}://{parsed.netloc}"

        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",  # noqa: C0301
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "Origin": origin,
        }

        if referer:
            headers["Referer"] = referer

        else:
            headers["Referer"] = origin

        return headers

    async def make_api_request(
        self,
        url: str,
        method: str = "get",
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        use_proxy: bool = False,
        timeout: int = 30,
        retries: int = 3,
    ) -> Optional[Dict]:
        """
        Make API request with retries using unified flow.

        Note: Now uses fetch_content_smart for consistent proxy/rendering handling.
        POST requests still use direct requests for body support.

        Args:
            url: API endpoint URL
            method: HTTP method (get, post)
            headers: Request headers
            json_data: JSON body for POST requests
            use_proxy: Whether to use proxy (deprecated, auto-handled for GET)
            timeout: Request timeout
            retries: Number of retries

        Returns:
            JSON response dict or None
        """
        headers = headers or {}
        if "User-Agent" not in headers:
            headers["User-Agent"] = self.user_agent.random

        # POST requests need direct handling for request body
        if method.lower() == "post":
            proxies = self.proxies if use_proxy else None
            for attempt in range(retries):
                try:
                    response = requests.post(
                        url,
                        json=json_data,
                        headers=headers,
                        proxies=proxies,
                        timeout=timeout,
                        verify=False,
                    )

                    if response.status_code in [200, 201, 202]:
                        try:
                            return response.json()
                        except Exception:
                            return {"text": response.text}
                    elif response.status_code == 429:
                        wait_time = 2**attempt
                        logger.warning(f"Rate limited. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"HTTP {response.status_code} for {url}")

                except requests.RequestException as e:
                    logger.error(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                    if attempt < retries - 1:
                        time.sleep(2**attempt)
            return None

        # GET requests use unified flow
        for attempt in range(retries):
            try:
                result = await self.fetch_content_smart(url, headers=headers, timeout=timeout)

                if result.get("error"):
                    if attempt < retries - 1:
                        logger.warning(f"Retry {attempt + 1}/{retries}: {result['error']}")
                        await asyncio.sleep(2**attempt)
                        continue
                    else:
                        logger.error(f"All retries failed: {result['error']}")
                        return None

                # Success - return content
                if result.get("is_json"):
                    return result["content"]
                else:
                    # Not JSON, return as text
                    return {"text": result.get("content", "")}

            except Exception as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2**attempt)

        return None

    async def fetch_html_content(
        self,
        url: str,
        headers: Optional[Dict] = None,
        use_proxy: bool = False,
        timeout: int = 30,
    ) -> Optional[str]:
        """
        Fetch HTML content from URL using unified flow.

        Note: Now uses fetch_content_smart for consistent proxy/rendering handling.
        The use_proxy parameter is deprecated and ignored (proxy auto-handled for 403).

        Args:
            url: Target URL
            headers: Request headers
            use_proxy: (Deprecated) Whether to use proxy - now auto-handled
            timeout: Request timeout

        Returns:
            HTML content string or None
        """
        headers = headers or {}
        if "User-Agent" not in headers:
            headers["User-Agent"] = self.user_agent.random

        # Use unified flow
        result = await self.fetch_content_smart(url, headers=headers, timeout=timeout)

        if result.get("error"):
            logger.error(f"Failed to fetch HTML from {url}: {result['error']}")
            return None

        # Return HTML content
        return result.get("content")

    def _has_captcha(self, html_content: str) -> bool:
        """Check if HTML content contains CAPTCHA indicators."""
        html_lower = html_content.lower()
        captcha_indicators = [
            "captcha",
            "cloudflare",
            "challenge",
            "verify you are human",
        ]
        return any(indicator in html_lower for indicator in captcha_indicators)

    def _get_random_proxy(self) -> Optional[Dict]:
        """Get a random proxy from ProxyManager (non-CDP proxies only)."""
        if not self.proxy_manager:
            # Fallback to legacy proxy
            return self.proxies if self.proxies else None

        active_proxies = [
            p
            for p in self.proxy_manager.list_proxies(active_only=True)
            if p.proxy_type != "cdp" and p.is_active
        ]

        if active_proxies:
            selected_proxy = random.choice(active_proxies)
            logger.info(
                f"Using proxy: {selected_proxy.name} ({selected_proxy.host}:{selected_proxy.port})"
            )
            return selected_proxy.to_requests_format()

        # Fallback to legacy proxy
        if self.proxies:
            logger.info("Using legacy proxy configuration")
            return self.proxies

        return None

    def _get_random_cdp_proxy(self):
        """Get a random CDP proxy from ProxyManager."""
        if not self.proxy_manager:
            return None

        cdp_proxies = [
            p
            for p in self.proxy_manager.list_proxies(active_only=True)
            if p.proxy_type == "cdp" and p.is_active
        ]

        if cdp_proxies:
            cdp_proxy = random.choice(cdp_proxies)
            logger.info(f"Using CDP proxy: {cdp_proxy.name} ({cdp_proxy.cdp_url})")
            return cdp_proxy

        return None

    async def _phase1_simple_request(
        self, url: str, headers: Dict, timeout: int
    ) -> tuple[requests.Response, str]:
        """Phase 1: Try simple HTTP request without proxy."""
        logger.info(f"Phase 1: Fetching {url} without proxy...")
        response = requests.get(
            url,
            headers=headers,
            proxies=None,
            timeout=timeout,
            verify=False,
        )
        content_type = response.headers.get("content-type", "").lower()
        return response, content_type

    async def _phase2_proxy_request(
        self, url: str, headers: Dict, timeout: int
    ) -> tuple[Optional[requests.Response], Optional[str]]:
        """Phase 2: Try request with proxy (for 403 errors)."""
        logger.info("Phase 2: HTTP 403 detected, trying with proxy...")

        proxy_dict = self._get_random_proxy()
        if not proxy_dict:
            logger.warning("No proxy available")
            return None, None

        try:
            response = requests.get(
                url,
                headers=headers,
                proxies=proxy_dict,
                timeout=timeout,
                verify=False,
            )
            content_type = response.headers.get("content-type", "").lower()
            
            if response.status_code == 200:
                logger.info(f"✓ Successfully fetched {url} with proxy")
            else:
                logger.warning(f"Proxy returned status {response.status_code}")
            
            return response, content_type

        except Exception as e:
            logger.warning(f"Proxy request failed: {e}")
            return None, None

    async def _phase3_process_content(
        self, response: requests.Response, content_type: str, result: Dict
    ) -> Optional[Dict]:
        """Phase 3: Process content based on type (JSON/HTML)."""
        # Handle JSON
        if "application/json" in content_type or "json" in content_type:
            logger.info("Phase 3: Processing JSON content")
            result["is_json"] = True
            try:
                result["content"] = response.json()
            except Exception:
                result["content"] = response.text
            return result

        # Handle HTML
        if "text/html" in content_type or "html" in content_type:
            logger.info("Phase 3: Processing HTML content")
            html_content = response.text
            result["content"] = html_content
            
            # Check if rendering needed
            if BrowserClient.needs_rendering(html_content):
                logger.info("JS rendering required")
                return None  # Signal that rendering is needed
            
            # No rendering needed
            result["rendered"] = False
            return result

        # Other content types
        logger.info(f"Phase 3: Processing other content type: {content_type}")
        result["content"] = response.text
        return result

    async def _phase4_render_with_playwright(
        self, url: str, timeout: int
    ) -> Optional[str]:
        """Phase 4a: Render with Playwright."""
        logger.info("Phase 4a: Rendering with Playwright...")
        try:
            rendered_html = await self.browser_client.render_page(
                url, timeout=timeout * 1000
            )

            # Check for CAPTCHA
            if self._has_captcha(rendered_html):
                logger.info("CAPTCHA detected, waiting 10 seconds...")
                await asyncio.sleep(10)
                rendered_html = await self.browser_client.render_page(
                    url, timeout=timeout * 1000
                )

            logger.info("✓ Successfully rendered with Playwright")
            return rendered_html

        except Exception as e:
            logger.warning(f"Playwright rendering failed: {e}")
            return None

    async def _phase4_render_with_cdp(
        self, url: str, timeout: int
    ) -> Optional[str]:
        """Phase 4b: Render with CDP (fallback for Playwright failures)."""
        logger.info("Phase 4b: Trying CDP rendering as fallback...")

        cdp_proxy = self._get_random_cdp_proxy()
        if not cdp_proxy:
            logger.warning("No CDP proxy available")
            return None

        try:
            rendered_html = await self.browser_client.render_page_with_cdp(
                url, cdp_url=cdp_proxy.cdp_url, timeout=timeout * 1000
            )

            if not rendered_html:
                return None

            # Check for CAPTCHA
            if self._has_captcha(rendered_html):
                logger.info("CAPTCHA detected, waiting 10 seconds...")
                await asyncio.sleep(10)
                rendered_html = await self.browser_client.render_page_with_cdp(
                    url, cdp_url=cdp_proxy.cdp_url, timeout=timeout * 1000
                )

            logger.info("✓ Successfully rendered with CDP")
            return rendered_html

        except Exception as e:
            logger.error(f"CDP rendering failed: {e}")
            return None

    async def fetch_content_smart(
        self,
        url: str,
        headers: Optional[Dict] = None,
        use_proxy: bool = False,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Smart content fetching following clean phase separation:
        Phase 1: Simple request
        Phase 2: Proxy (if 403)
        Phase 3: Process content type
        Phase 4: Render if needed (Playwright → CDP fallback)

        Args:
            url: Target URL
            headers: Request headers
            use_proxy: Whether to use proxy (deprecated, auto-handled)
            timeout: Request timeout

        Returns:
            Dict with content, content_type, rendered flag, etc.
        """
        result = {
            "url": url,
            "content": None,
            "content_type": None,
            "is_json": False,
            "rendered": False,
            "status_code": None,
            "error": None,
        }

        # Prepare headers
        headers = headers or {}
        if "User-Agent" not in headers:
            headers["User-Agent"] = self.user_agent.random
        if not headers:
            headers = self._get_browser_headers(url)
        elif "User-Agent" not in headers:
            browser_headers = self._get_browser_headers(url)
            headers.update(browser_headers)

        try:
            # PHASE 1: Simple request
            response, content_type = await self._phase1_simple_request(
                url, headers, timeout
            )
            result["status_code"] = response.status_code
            result["content_type"] = content_type

            # PHASE 2: Proxy (if 403)
            if response.status_code == 403:
                proxy_response, proxy_content_type = await self._phase2_proxy_request(
                    url, headers, timeout
                )
                if proxy_response and proxy_response.status_code == 200:
                    response = proxy_response
                    content_type = proxy_content_type
                    result["status_code"] = response.status_code
                    result["content_type"] = content_type

            # Check status
            if response.status_code != 200:
                result["error"] = f"HTTP {response.status_code}"
                return result

            # PHASE 3: Process content type
            processed_result = await self._phase3_process_content(
                response, content_type, result
            )

            if processed_result:
                # Content processed successfully (JSON or HTML without rendering)
                return processed_result

            # PHASE 4: Rendering needed
            # Try Playwright first
            rendered_html = await self._phase4_render_with_playwright(url, timeout)

            if rendered_html:
                result["content"] = rendered_html
                result["rendered"] = True
                return result

            # Playwright failed, try CDP
            rendered_html = await self._phase4_render_with_cdp(url, timeout)

            if rendered_html:
                result["content"] = rendered_html
                result["rendered"] = True
                return result

            # All rendering failed, return original HTML
            logger.warning("All rendering methods failed, returning original HTML")
            result["content"] = response.text
            result["rendered"] = False
            return result

        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            result["error"] = str(e)

            # Fallback: Try rendering
            try:
                logger.info("Request failed, trying Playwright as fallback...")
                rendered_html = await self._phase4_render_with_playwright(url, timeout)
                if rendered_html:
                    result["content"] = rendered_html
                    result["rendered"] = True
                    result["error"] = None
                    return result
            except Exception:
                pass

            return result
