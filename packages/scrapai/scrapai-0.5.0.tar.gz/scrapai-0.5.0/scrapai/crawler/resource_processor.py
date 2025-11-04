"""

Resource Processor - Process individual resources with correct method names

"""



import asyncio

from typing import Any, Optional, Dict

import logging

from bs4 import BeautifulSoup



from ..config.schema import ResourceConfig, ResourceType

from ..utils.http_client import HTTPClient

from ..utils.html_extractor import HTMLExtractor

from ..utils.data_transformer import DataTransformer



logger = logging.getLogger(__name__)





class ResourceProcessor:

    """

    Process individual scraping resources.

    Uses properly named methods for each operation.

    """



    def __init__(self, proxies: Optional[Dict] = None, browser=None, context=None):

        """

        Initialize resource processor.



        Args:

            proxies: Proxy configuration

            browser: Playwright browser

            context: Browser context

        """

        self.http_client = HTTPClient(proxies)

        self.html_extractor = HTMLExtractor()

        self.data_transformer = DataTransformer()

        self.browser = browser

        self.context = context



    async def process_resource(self, resource: ResourceConfig, utils_module=None) -> Any:

        """

        Process a single resource and extract data.



        Args:

            resource: ResourceConfig to process

            utils_module: Optional custom utils module



        Returns:

            Extracted data or None if failed

        """

        try:

            # Route to appropriate processor based on resource type

            if resource.resource_type in [ResourceType.API_JSON, ResourceType.API_GRAPHQL]:

                return await self.process_api_resource(resource, utils_module)



            elif resource.resource_type == ResourceType.HTML_STATIC:

                return await self.process_static_html_resource(resource, utils_module)



            elif resource.resource_type == ResourceType.HTML_RENDERED:

                return await self.process_rendered_html_resource(resource, utils_module)



            elif resource.resource_type == ResourceType.HTML_CAPTCHA:

                return await self.process_captcha_html_resource(resource, utils_module)



            elif resource.resource_type == ResourceType.CUSTOM_METHOD:

                return await self.process_custom_method_resource(resource, utils_module)



            else:

                logger.error(f"Unknown resource type: {resource.resource_type}")

                return None



        except Exception as e:

            logger.error(f"Resource processing failed for {resource.url}: {e}")

            return None



    async def process_api_resource(self, resource: ResourceConfig, utils_module=None) -> Any:

        """

        Process API resource (JSON/GraphQL).

        Priority: api_path -> (no xpath/path for API) -> extra_method -> value



        Args:

            resource: ResourceConfig with API details

            utils_module: Optional custom utils



        Returns:

            Extracted value

        """

        # Priority 4: extra_method (skip API call if using custom method)

        if resource.extra_method:

            return await self.process_custom_method_resource(resource, utils_module)



        # Priority 5: value (static value)

        if resource.value is not None:

            return resource.value



        # Make API call

        response_data = await self.http_client.make_api_request(

            url=resource.url,

            method=resource.method,

            headers=resource.headers,

            json_data=resource.request_data,

            use_proxy=resource.use_proxy,

            timeout=resource.timeout,

            retries=resource.retries

        )



        if not response_data:

            return None



        # Priority 1: Extract using api_path (automatic, direct)

        if resource.api_path:

            value = self.data_transformer.extract_from_json_path(

                response_data,

                resource.api_path

            )

        else:

            value = response_data



        # Apply transformation actions (only for transforming extracted value)

        for method_name in resource.actions_methods:

            value = self._apply_method(value, method_name, utils_module)



        return value



    async def process_static_html_resource(self, resource: ResourceConfig, utils_module=None) -> Any:

        """

        Process static HTML resource (no JavaScript).

        Priority: xpath -> path -> extra_method -> value



        Args:

            resource: ResourceConfig with HTML details

            utils_module: Optional custom utils



        Returns:

            Extracted value

        """

        # Priority 4: extra_method

        if resource.extra_method:

            return await self.process_custom_method_resource(resource, utils_module)



        # Priority 5: value (static value)

        if resource.value is not None:

            return resource.value



        # Fetch HTML

        html_content = await self.http_client.fetch_html_content(

            url=resource.url,

            headers=resource.headers,

            use_proxy=resource.use_proxy,

            timeout=resource.timeout

        )



        if not html_content:

            return None



        # Priority 2: Extract using xpath (automatic, direct)

        if resource.xpath:

            value = self.html_extractor.extract_with_xpath(html_content, resource.xpath)

        # Priority 3: Extract using path (automatic, direct)

        elif resource.path:

            # Pre-actions can operate on soup object for special operations (e.g., count table rows)

            soup = BeautifulSoup(html_content, 'html.parser') if resource.pre_actions_methods else None



            # Apply pre-actions on soup if needed (rare cases like counting table rows)

            for method_name in resource.pre_actions_methods:

                if soup is not None and utils_module and hasattr(utils_module, method_name):

                    method = getattr(utils_module, method_name)

                    # Pre-action may return modified soup or a value

                    result = method(soup)

                    if result is not None:

                        # If pre-action returned a value, use it

                        if not isinstance(result, type(soup)):

                            value = result

                            break

                        soup = result

                else:

                    logger.warning(f"Pre-action {method_name} requires soup object but not available")



            # Extract using path if pre-actions didn't return a value

            if 'value' not in locals():

                value = self.html_extractor.extract_with_beautifulsoup_path(

                    html_content, resource.path, soup=soup if soup else None

                )

        else:

            logger.warning("No extraction method specified for HTML resource")

            return None



        # Apply transformation actions (only for transforming extracted value)

        for method_name in resource.actions_methods:

            value = self._apply_method(value, method_name, utils_module)



        return value



    async def process_rendered_html_resource(self, resource: ResourceConfig, utils_module=None) -> Any:

        """

        Process HTML resource requiring JavaScript rendering.

        Priority: xpath -> path -> extra_method -> value



        Args:

            resource: ResourceConfig with rendering details

            utils_module: Optional custom utils



        Returns:

            Extracted value

        """

        # Priority 4: extra_method

        if resource.extra_method:

            return await self.process_custom_method_resource(resource, utils_module)



        # Priority 5: value (static value)

        if resource.value is not None:

            return resource.value



        if not self.browser or not self.context:

            logger.error("Browser not initialized for rendered HTML")

            return None



        # Render page with Playwright

        html_content = await self.html_extractor.render_page_with_browser(

            url=resource.url,

            browser=self.browser,

            context=self.context,

            sleep_time=resource.sleep_time,

            locator_click=resource.locator_click

        )



        if not html_content:

            return None



        # Priority 2: Extract using xpath (automatic, direct)

        if resource.xpath:

            value = self.html_extractor.extract_with_xpath(html_content, resource.xpath)

        # Priority 3: Extract using path (automatic, direct)

        elif resource.path:

            # Pre-actions can operate on soup object for special operations

            soup = BeautifulSoup(html_content, 'html.parser') if resource.pre_actions_methods else None



            # Apply pre-actions on soup if needed (rare cases)

            for method_name in resource.pre_actions_methods:

                if soup is not None and utils_module and hasattr(utils_module, method_name):

                    method = getattr(utils_module, method_name)

                    result = method(soup)

                    if result is not None and not isinstance(result, type(soup)):

                        value = result

                        break

                    soup = result



            # Extract using path if pre-actions didn't return a value

            if 'value' not in locals():

                value = self.html_extractor.extract_with_beautifulsoup_path(

                    html_content, resource.path, soup=soup if soup else None

                )

        else:

            logger.warning("No extraction method specified for rendered HTML resource")

            return None



        # Apply transformation actions (only for transforming extracted value)

        for method_name in resource.actions_methods:

            value = self._apply_method(value, method_name, utils_module)



        return value



    async def process_captcha_html_resource(self, resource: ResourceConfig, utils_module=None) -> Any:

        """

        Process HTML resource with CAPTCHA.

        Priority: xpath -> path -> extra_method -> value



        Args:

            resource: ResourceConfig with CAPTCHA details

            utils_module: Optional custom utils



        Returns:

            Extracted value

        """

        # Priority 4: extra_method

        if resource.extra_method:

            return await self.process_custom_method_resource(resource, utils_module)



        # Priority 5: value (static value)

        if resource.value is not None:

            return resource.value



        if not self.browser or not self.context:

            logger.error("Browser not initialized for CAPTCHA solving")

            return None



        # Render with CAPTCHA solving

        html_content = await self.html_extractor.render_page_with_captcha_solving(

            url=resource.url,

            browser=self.browser,

            context=self.context,

            sleep_time=resource.sleep_time,

            locator_click=resource.locator_click

        )



        if not html_content:

            return None



        # Priority 2: Extract using xpath (automatic, direct)

        if resource.xpath:

            value = self.html_extractor.extract_with_xpath(html_content, resource.xpath)

        # Priority 3: Extract using path (automatic, direct)

        elif resource.path:

            # Pre-actions can operate on soup object for special operations

            soup = BeautifulSoup(html_content, 'html.parser') if resource.pre_actions_methods else None



            # Apply pre-actions on soup if needed (rare cases)

            for method_name in resource.pre_actions_methods:

                if soup is not None and utils_module and hasattr(utils_module, method_name):

                    method = getattr(utils_module, method_name)

                    result = method(soup)

                    if result is not None and not isinstance(result, type(soup)):

                        value = result

                        break

                    soup = result



            # Extract using path if pre-actions didn't return a value

            if 'value' not in locals():

                value = self.html_extractor.extract_with_beautifulsoup_path(

                    html_content, resource.path, soup=soup if soup else None

                )

        else:

            logger.warning("No extraction method specified for CAPTCHA HTML resource")

            return None



        # Apply transformation actions (only for transforming extracted value)

        for method_name in resource.actions_methods:

            value = self._apply_method(value, method_name, utils_module)



        return value



    async def process_custom_method_resource(self, resource: ResourceConfig, utils_module=None) -> Any:

        """

        Process resource using custom method from utils.



        Args:

            resource: ResourceConfig with custom method name

            utils_module: Required custom utils module



        Returns:

            Extracted value

        """

        if not utils_module or not resource.extra_method:

            logger.error("Custom method resource requires utils_module and extra_method")

            return None



        if not hasattr(utils_module, resource.extra_method):

            logger.error(f"Utils module missing method: {resource.extra_method}")

            return None



        # Call custom method

        method = getattr(utils_module, resource.extra_method)



        kwargs = resource.extra_method_kwargs or {}

        kwargs["url"] = resource.url



        if asyncio.iscoroutinefunction(method):

            value = await method(**kwargs)

        else:

            value = method(**kwargs)



        return value



    def _apply_method(self, value: Any, method_name: str, utils_module=None) -> Any:

        """

        Apply transformation method to value.



        Args:

            value: Current value

            method_name: Method to apply

            utils_module: Optional custom utils



        Returns:

            Transformed value

        """

        # Check custom utils first

        if utils_module and hasattr(utils_module, method_name):

            method = getattr(utils_module, method_name)

            return method(value)



        # Use built-in transformer

        if hasattr(self.data_transformer, method_name):

            method = getattr(self.data_transformer, method_name)

            return method(value)



        logger.warning(f"Method not found: {method_name}")

        return value
