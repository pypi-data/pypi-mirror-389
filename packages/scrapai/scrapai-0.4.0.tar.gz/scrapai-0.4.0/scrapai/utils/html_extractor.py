"""

HTML Extractor - Extract data from HTML with properly named methods

"""



import asyncio

import logging

from typing import Optional, List, Dict, Any

from bs4 import BeautifulSoup

from lxml import etree



logger = logging.getLogger(__name__)



try:

    from playwright_stealth import stealth_async

    HAS_STEALTH = True

except ImportError:

    HAS_STEALTH = False





class HTMLExtractor:

    """Extract data from HTML using various methods"""



    def extract_with_xpath(self, html: str, xpath: str) -> Optional[str]:

        """

        Extract value using XPath.



        Args:

            html: HTML content

            xpath: XPath expression



        Returns:

            Extracted text or None

        """

        try:

            tree = etree.HTML(html)

            result = tree.xpath(xpath)



            if result:

                if isinstance(result, list):

                    # Return first element

                    elem = result[0]

                    if isinstance(elem, str):

                        return elem

                    elif hasattr(elem, 'text'):

                        return elem.text

                    else:

                        return str(elem)

                else:

                    return str(result)



        except Exception as e:

            logger.error(f"XPath extraction failed: {e}")



        return None



    def extract_with_beautifulsoup_path(self, html: str, path: List[Dict], soup=None) -> Optional[str]:

        """

        Extract value using BeautifulSoup path.



        Args:

            html: HTML content (required if soup not provided)

            path: List of path steps [{"tag": "div", "attribute": {"class": "value"}}]

            soup: Optional pre-parsed BeautifulSoup object



        Returns:

            Extracted text or None

        """

        try:

            if soup is None:

                soup = BeautifulSoup(html, "html.parser")

            current = soup



            for step in path:

                tag = step.get("tag")

                attrs = step.get("attribute", {})



                if tag:

                    current = current.find(tag, attrs=attrs)

                    if not current:

                        return None



            if current:

                return current.get_text(strip=True)



        except Exception as e:

            logger.error(f"BeautifulSoup path extraction failed: {e}")



        return None



    def extract_with_css_selector(self, html: str, selector: str) -> Optional[str]:

        """

        Extract value using CSS selector.



        Args:

            html: HTML content

            selector: CSS selector



        Returns:

            Extracted text or None

        """

        try:

            soup = BeautifulSoup(html, "html.parser")

            elem = soup.select_one(selector)



            if elem:

                return elem.get_text(strip=True)



        except Exception as e:

            logger.error(f"CSS selector extraction failed: {e}")



        return None



    async def render_page_with_browser(

        self,

        url: str,

        browser: Any,

        context: Any,

        sleep_time: int = 5,

        locator_click: Optional[str] = None

    ) -> Optional[str]:

        """

        Render page using Playwright browser.



        Args:

            url: URL to render

            browser: Playwright browser

            context: Browser context

            sleep_time: Wait time in seconds

            locator_click: CSS selector to click



        Returns:

            Rendered HTML content

        """

        page = await context.new_page()



        try:

            if HAS_STEALTH:

                await stealth_async(page)



            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            await page.wait_for_load_state("load")

            await page.wait_for_timeout(sleep_time * 1000)



            if locator_click:

                try:

                    await page.click(locator_click)

                    await page.wait_for_timeout(5000)

                except Exception as e:

                    logger.warning(f"Click failed: {e}")



            return await page.content()



        except Exception as e:

            logger.error(f"Page rendering failed: {e}")

            return None

        finally:

            await page.close()



    async def render_page_with_captcha_solving(

        self,

        url: str,

        browser: Any,

        context: Any,

        sleep_time: int = 15,

        locator_click: Optional[str] = None

    ) -> Optional[str]:

        """

        Render page with CAPTCHA solving.



        Args:

            url: URL to render

            browser: Playwright browser with CAPTCHA solving

            context: Browser context

            sleep_time: Wait time in seconds

            locator_click: CSS selector to click



        Returns:

            Rendered HTML content

        """

        page = await context.new_page()



        try:

            if HAS_STEALTH:

                await stealth_async(page)



            await page.goto(url, wait_until="domcontentloaded", timeout=60000)



            # Solve CAPTCHA using CDP

            client = await page.context.new_cdp_session(page)

            try_count = 3



            while try_count > 0:

                solve_res = await client.send('Captcha.waitForSolve', {'detectTimeout': 10000})

                if "solve_failed" not in solve_res.get('status', ''):

                    break

                try_count -= 1

                logger.warning(f"CAPTCHA solving failed, retrying {try_count} more time(s)...")



            await page.wait_for_timeout(sleep_time * 1000)



            if locator_click:

                try:

                    await page.click(locator_click)

                    await page.wait_for_timeout(5000)

                except Exception as e:

                    logger.warning(f"Click failed: {e}")



            return await page.content()



        except Exception as e:

            logger.error(f"CAPTCHA page rendering failed: {e}")

            return None

        finally:

            await page.close()
