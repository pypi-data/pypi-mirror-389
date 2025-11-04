"""

Browser Client - Playwright wrapper for rendering JavaScript-heavy pages

"""



import asyncio

import json

import re

from typing import Dict, Any, Optional, List

from urllib.parse import urlparse

from fake_useragent import UserAgent

from playwright.async_api import async_playwright, Browser, Page





class BrowserClient:

    """Playwright-based browser client for rendering JavaScript content"""



    def __init__(self, headless: bool = True):

        """

        Initialize browser client.



        Args:

            headless: Run browser in headless mode

        """

        self.headless = headless

        self._browser: Optional[Browser] = None



    async def __aenter__(self):

        """Async context manager entry"""

        self.playwright = await async_playwright().start()

        self._browser = await self.playwright.chromium.launch(headless=self.headless)

        return self



    async def __aexit__(self, exc_type, exc_val, exc_tb):

        """Async context manager exit"""

        if self._browser:

            await self._browser.close()

        await self.playwright.stop()



    async def render_page(

        self,

        url: str,

        wait_until: str = 'networkidle',

        timeout: int = 30000,

        wait_after_load: float = 10

    ) -> str:

        """

        Render page with JavaScript execution.



        Args:

            url: Target URL

            wait_until: Wait condition ('load', 'domcontentloaded', 'networkidle')

            timeout: Navigation timeout in milliseconds

            wait_after_load: Additional wait time after load in seconds



        Returns:

            Rendered HTML content

        """

        async with async_playwright() as p:

            browser = await p.chromium.launch(headless=self.headless)



            # Create context with browser-like headers and SSL verification disabled

            ua = UserAgent()



            # Parse URL for origin

            parsed = urlparse(url)

            origin = f"{parsed.scheme}://{parsed.netloc}"



            # Browser-like headers

            browser_headers = {

                "User-Agent": ua.random,

                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",

                "Accept-Language": "en-US,en;q=0.9",

                "Accept-Encoding": "gzip, deflate, br",

                "Connection": "keep-alive",

                "Upgrade-Insecure-Requests": "1",

                "Sec-Fetch-Dest": "document",

                "Sec-Fetch-Mode": "navigate",

                "Sec-Fetch-Site": "none",

                "Sec-Fetch-User": "?1",

                "Referer": origin,

                "Origin": origin,

            }



            context = await browser.new_context(

                ignore_https_errors=True,

                extra_http_headers=browser_headers

            )

            page = await context.new_page()



            try:

                # Navigate to page (SSL errors will be ignored)

                await page.goto(url, wait_until='load', timeout=timeout)



                # Wait for dynamic content

                if wait_after_load > 0:

                    await asyncio.sleep(wait_after_load)



                # Get rendered HTML

                content = await page.content()



                return content

            finally:

                await context.close()

                await browser.close()



    async def intercept_apis(

        self,

        url: str,

        search_keywords: Optional[List[str]] = None,

        timeout: int = 30000,

        wait_after_load: float = 3.0

    ) -> Dict[str, Any]:

        """

        Load page and intercept all API calls.



        Args:

            url: Target URL

            search_keywords: Optional keywords to search in responses

            timeout: Navigation timeout in milliseconds

            wait_after_load: Additional wait time for API calls



        Returns:

            Dict with discovered APIs and matches

        """

        api_calls = []



        async with async_playwright() as p:

            browser = await p.chromium.launch(headless=self.headless)



            # Create context with browser-like headers and SSL verification disabled

            ua = UserAgent()



            # Parse URL for origin

            parsed = urlparse(url)

            origin = f"{parsed.scheme}://{parsed.netloc}"



            # Browser-like headers

            browser_headers = {

                "User-Agent": ua.random,

                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",

                "Accept-Language": "en-US,en;q=0.9",

                "Accept-Encoding": "gzip, deflate, br",

                "Connection": "keep-alive",

                "Upgrade-Insecure-Requests": "1",

                "Sec-Fetch-Dest": "document",

                "Sec-Fetch-Mode": "navigate",

                "Sec-Fetch-Site": "none",

                "Sec-Fetch-User": "?1",

                "Referer": origin,

                "Origin": origin,

            }



            context = await browser.new_context(

                ignore_https_errors=True,

                extra_http_headers=browser_headers

            )

            page = await context.new_page()



            try:

                # Set up response interceptor

                async def handle_response(response):

                    try:

                        content_type = response.headers.get('content-type', '')

                        if 'json' in content_type or 'application/json' in content_type:

                            try:

                                body = await response.json()



                                # Get request headers

                                request_headers = {}

                                for header_name, header_value in response.request.headers.items():

                                    request_headers[header_name] = header_value



                                # Get response headers

                                response_headers = {}

                                for header_name, header_value in response.headers.items():

                                    response_headers[header_name] = header_value



                                api_info = {

                                    'url': response.url,

                                    'status': response.status,

                                    'method': response.request.method,

                                    'request_headers': request_headers,

                                    'response_headers': response_headers,

                                    'response_preview': str(body)[:500]

                                }



                                # Check if response contains search keywords

                                if search_keywords:

                                    body_str = json.dumps(body).lower()

                                    matches = [kw for kw in search_keywords if kw.lower() in body_str]

                                    if matches:

                                        api_info['matched_keywords'] = matches

                                        api_info['full_response'] = body



                                api_calls.append(api_info)

                            except:

                                pass

                    except Exception:

                        pass



                page.on('response', handle_response)



                # Navigate to page

                await page.goto(url, wait_until='networkidle', timeout=timeout)



                # Wait for delayed API calls (default 30 seconds for API discovery)

                if wait_after_load > 0:

                    await asyncio.sleep(wait_after_load)



                # Separate matched and unmatched

                matched = [api for api in api_calls if 'matched_keywords' in api]

                unmatched = [api for api in api_calls if 'matched_keywords' not in api]



                return {

                    "success": True,

                    "total_apis": len(api_calls),

                    "matched_apis": matched,

                    "all_apis": api_calls,

                    "summary": {

                        "total": len(api_calls),

                        "matched": len(matched),

                        "unmatched": len(unmatched)

                    }

                }

            finally:

                await context.close()

                await browser.close()



    @staticmethod

    def needs_rendering(html_content: str) -> bool:

        """

        Check if HTML content indicates JavaScript rendering is required.



        Args:

            html_content: HTML content to check



        Returns:

            True if JS rendering is likely needed

        """

        indicators = [

            # Empty or minimal body

            '<body></body>',

            '<body />',

            # Common JS frameworks

            'id="root"',

            'id="app"',

            'ng-app',

            'data-reactroot',

            'data-react-helmet',

            'data-reactid',

            # Client-side routing

            'window.__INITIAL_STATE__',

            'window.__PRELOADED_STATE__',

            # Webpack/build indicators

            '__webpack',

            'webpackJsonp',

            # Loading messages

            'Loading...',

            'Please enable JavaScript',

            'JavaScript is required',

            'This app works best with JavaScript enabled',

        ]



        # Check for indicators

        for indicator in indicators:

            if indicator in html_content:

                return True



        # Check if content is suspiciously short but has scripts

        if len(html_content) < 1000 and '<script' in html_content:

            content_without_scripts = re.sub(

                r'<script[^>]*>.*?</script>',

                '',

                html_content,

                flags=re.DOTALL | re.IGNORECASE

            )

            if len(content_without_scripts.strip()) < 500:

                return True



        return False





class BrowserPool:

    """Pool of browser instances for concurrent rendering"""



    def __init__(self, pool_size: int = 3, headless: bool = True):

        """

        Initialize browser pool.



        Args:

            pool_size: Number of browser instances in pool

            headless: Run browsers in headless mode

        """

        self.pool_size = pool_size

        self.headless = headless

        self._clients: List[BrowserClient] = []



    async def __aenter__(self):

        """Initialize pool"""

        for _ in range(self.pool_size):

            client = BrowserClient(headless=self.headless)

            await client.__aenter__()

            self._clients.append(client)

        return self



    async def __aexit__(self, exc_type, exc_val, exc_tb):

        """Cleanup pool"""

        for client in self._clients:

            await client.__aexit__(exc_type, exc_val, exc_tb)



    async def render_page(self, url: str, **kwargs) -> str:

        """Render page using available client from pool"""

        if not self._clients:

            raise RuntimeError("Browser pool not initialized")



        # Use first available client (round-robin could be added)

        client = self._clients[0]

        return await client.render_page(url, **kwargs)
