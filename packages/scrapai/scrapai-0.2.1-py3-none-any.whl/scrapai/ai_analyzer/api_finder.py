"""

API Finder - Automatically discover API endpoints from web pages using Playwright

Based on daap-esg implementation

"""

import asyncio

import json

from typing import List, Dict, Optional

from ..utils.browser_client import BrowserClient


class APIFinder:
    """Discovers API endpoints by loading pages with Playwright and intercepting network calls"""

    def __init__(self, base_url: str):

        """

        Initialize API finder.



        Args:

            base_url: Base URL of the website

        """

        self.base_url = base_url

        self.browser_client = BrowserClient(headless=True)

    async def render_page(self, url: str) -> str:

        """

        Render page with Playwright to execute JavaScript.



        Args:

            url: Target URL



        Returns:

            Rendered HTML content

        """

        return await self.browser_client.render_page(url)

    async def find_apis(self, url: str, search_keywords: Optional[List[str]] = None,
                        timeout_seconds: float = 30.0) -> Dict:  # noqa: C0301

        """

        Load URL with Playwright, intercept all API calls, log responses.



        Args:

            url: Website URL to load

            search_keywords: Optional list of keywords to search in API responses

            timeout_seconds: Wait time after page load for API calls (default: 30 seconds)



        Returns:

            Dict with discovered APIs and matches

        """

        return await self.browser_client.intercept_apis(url, search_keywords, wait_after_load=timeout_seconds)

    def discover_apis_from_page(self, html_content: str, keywords: Optional[List[str]] = None) -> List[Dict]:

        """

        Legacy method for compatibility - runs async find_apis synchronously.



        Args:

            html_content: HTML content (not used, we load the page directly)

            keywords: Optional keywords to filter relevant APIs



        Returns:

            List of discovered API endpoint information

        """

        # Run async method synchronously

        try:

            loop = asyncio.get_event_loop()

        except RuntimeError:

            loop = asyncio.new_event_loop()

            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(self.find_apis(self.base_url, keywords))

        return result.get('all_apis', [])
