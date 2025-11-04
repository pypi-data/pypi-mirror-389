"""

HTTP Client - Properly named methods for API and web requests

"""



import requests

import time

import asyncio

import logging

import urllib3

from typing import Dict, Any, Optional

from urllib.parse import urlparse

from fake_useragent import UserAgent



from .browser_client import BrowserClient



# Suppress SSL warnings when verify=False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



logger = logging.getLogger(__name__)





class HTTPClient:

    """HTTP client for API requests and HTML fetching with smart rendering"""



    def __init__(self, proxies: Optional[Dict] = None):

        """

        Initialize HTTP client.



        Args:

            proxies: Proxy configuration dict

        """

        self.proxies = proxies or {}

        self.user_agent = UserAgent()

        self.browser_client = BrowserClient(headless=True)

        self._user_agent_index = 0



    def _get_browser_headers(self, url: str, referer: Optional[str] = None) -> Dict[str, str]:

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

        retries: int = 3

    ) -> Optional[Dict]:

        """

        Make API request with retries.



        Args:

            url: API endpoint URL

            method: HTTP method (get, post)

            headers: Request headers

            json_data: JSON body for POST requests

            use_proxy: Whether to use proxy

            timeout: Request timeout

            retries: Number of retries



        Returns:

            JSON response dict or None

        """

        headers = headers or {}

        if "User-Agent" not in headers:

            headers["User-Agent"] = self.user_agent.random



        proxies = self.proxies if use_proxy else None



        for attempt in range(retries):

            try:

                if method.lower() == "post":

                    response = requests.post(

                        url,

                        json=json_data,

                        headers=headers,

                        proxies=proxies,

                        timeout=timeout,

                        verify=False  # Bypass SSL verification for expired certs

                    )

                else:

                    response = requests.get(

                        url,

                        headers=headers,

                        proxies=proxies,

                        timeout=timeout,

                        verify=False  # Bypass SSL verification for expired certs

                    )



                if response.status_code in [200, 201, 202]:

                    try:

                        return response.json()

                    except:

                        return {"text": response.text}



                elif response.status_code == 429:

                    wait_time = 2 ** attempt

                    logger.warning(f"Rate limited. Waiting {wait_time}s...")

                    time.sleep(wait_time)



                else:

                    logger.error(f"HTTP {response.status_code} for {url}")



            except requests.RequestException as e:

                logger.error(f"Request failed (attempt {attempt + 1}/{retries}): {e}")

                if attempt < retries - 1:

                    time.sleep(2 ** attempt)



        return None



    async def fetch_html_content(

        self,

        url: str,

        headers: Optional[Dict] = None,

        use_proxy: bool = False,

        timeout: int = 30

    ) -> Optional[str]:

        """

        Fetch HTML content from URL.



        Args:

            url: Target URL

            headers: Request headers

            use_proxy: Whether to use proxy

            timeout: Request timeout



        Returns:

            HTML content string or None

        """

        headers = headers or {}

        if "User-Agent" not in headers:

            headers["User-Agent"] = self.user_agent.random



        proxies = self.proxies if use_proxy else None



        # Add browser-like headers if not provided

        if not headers:

            headers = self._get_browser_headers(url)

        elif "User-Agent" not in headers:

            browser_headers = self._get_browser_headers(url)

            headers.update(browser_headers)



        try:

            response = requests.get(

                url,

                headers=headers,

                proxies=proxies,

                timeout=timeout,

                verify=False  # Bypass SSL verification for expired certs

            )



            if response.status_code == 200:

                return response.text

            else:

                logger.error(f"HTTP {response.status_code} for {url}")



        except requests.RequestException as e:

            logger.error(f"Failed to fetch HTML from {url}: {e}")



        return None



    async def fetch_content_smart(

        self,

        url: str,

        headers: Optional[Dict] = None,

        use_proxy: bool = False,

        timeout: int = 30

    ) -> Dict[str, Any]:

        """

        Smart content fetching - tries simple request first, renders if needed.



        Args:

            url: Target URL

            headers: Request headers

            use_proxy: Whether to use proxy

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

            "error": None

        }



        headers = headers or {}

        if "User-Agent" not in headers:

            headers["User-Agent"] = self.user_agent.random



        proxies = self.proxies if use_proxy else None



        # Add browser-like headers if not provided

        if not headers:

            headers = self._get_browser_headers(url)

        elif "User-Agent" not in headers:

            browser_headers = self._get_browser_headers(url)

            headers.update(browser_headers)



        try:

            # Step 1: Try simple request

            response = requests.get(

                url,

                headers=headers,

                proxies=proxies,

                timeout=timeout,

                verify=False  # Bypass SSL verification for expired certs

            )



            result["status_code"] = response.status_code

            content_type = response.headers.get('content-type', '').lower()

            result["content_type"] = content_type



            # Handle 403 Forbidden - try browser rendering
            if response.status_code == 403:
                logger.info(f"HTTP 403 for {url}, attempting browser rendering...")
                try:
                    rendered_html = await self.browser_client.render_page(
                        url,
                        timeout=timeout * 1000
                    )
                    result["content"] = rendered_html
                    result["rendered"] = True
                    result["status_code"] = 200  # Mark as success after rendering
                    result["error"] = None
                    
                    # Check for CAPTCHA in rendered content
                    html_lower = rendered_html.lower()
                    if any(indicator in html_lower for indicator in ["captcha", "cloudflare", "challenge", "verify you are human"]):
                        logger.info(f"CAPTCHA detected in rendered content for {url}, waiting 10 seconds...")
                        await asyncio.sleep(10)
                        # Re-render after wait
                        rendered_html = await self.browser_client.render_page(
                            url,
                            timeout=timeout * 1000
                        )
                        result["content"] = rendered_html
                    
                    return result
                except Exception as render_error:
                    logger.warning(f"Browser rendering failed for 403: {render_error}")
                    result["error"] = f"HTTP 403 and render failed: {render_error}"
                    return result

            if response.status_code != 200:

                result["error"] = f"HTTP {response.status_code}"

                return result



            # Step 2: Handle JSON responses

            if 'application/json' in content_type or 'json' in content_type:

                result["is_json"] = True

                try:

                    result["content"] = response.json()

                except:

                    result["content"] = response.text

                return result



            # Step 3: Handle HTML - check if rendering needed

            if 'text/html' in content_type or 'html' in content_type:

                html_content = response.text
                
                # Check for CAPTCHA before processing
                html_lower = html_content.lower()
                has_captcha = any(indicator in html_lower for indicator in ["captcha", "cloudflare", "challenge", "verify you are human"])
                
                if has_captcha:
                    logger.info(f"CAPTCHA detected in HTML for {url}, waiting 10 seconds then rendering...")
                    await asyncio.sleep(10)
                    # Force rendering for CAPTCHA pages
                    try:
                        rendered_html = await self.browser_client.render_page(
                            url,
                            timeout=timeout * 1000
                        )
                        result["content"] = rendered_html
                        result["rendered"] = True
                        return result
                    except Exception as render_error:
                        logger.warning(f"CAPTCHA render failed: {render_error}, using original HTML")
                        result["content"] = html_content
                        result["rendered"] = False
                        return result



                # Check if JavaScript rendering is required

                if BrowserClient.needs_rendering(html_content):

                    logger.info(f"JS rendering required for {url}, using Playwright...")

                    try:

                        rendered_html = await self.browser_client.render_page(

                            url,

                            timeout=timeout * 1000  # Convert to milliseconds

                        )

                        result["content"] = rendered_html

                        result["rendered"] = True
                        
                        # Check for CAPTCHA in rendered content
                        rendered_lower = rendered_html.lower()
                        if any(indicator in rendered_lower for indicator in ["captcha", "cloudflare", "challenge", "verify you are human"]):
                            logger.info(f"CAPTCHA detected in rendered content, waiting 10 seconds...")
                            await asyncio.sleep(10)
                            # Re-render after wait
                            rendered_html = await self.browser_client.render_page(
                                url,
                                timeout=timeout * 1000
                            )
                            result["content"] = rendered_html

                    except Exception as render_error:

                        logger.warning(f"Rendering failed: {render_error}, using original HTML")

                        result["content"] = html_content

                        result["rendered"] = False

                else:

                    result["content"] = html_content

                    result["rendered"] = False



                return result



            # Step 4: Other content types

            result["content"] = response.text

            return result



        except requests.RequestException as e:

            logger.error(f"Request failed for {url}: {e}")

            result["error"] = str(e)



            # Fallback: Try rendering with Playwright

            try:

                logger.info(f"Fallback: Trying Playwright rendering for {url}")

                rendered_html = await self.browser_client.render_page(url, timeout=timeout * 1000)

                result["content"] = rendered_html

                result["rendered"] = True

                result["error"] = None

            except Exception as render_error:

                result["error"] = f"Request failed: {e}. Render failed: {render_error}"



            return result
