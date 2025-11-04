"""

AI Agent Tools - All tools available to the AI agent

"""

import re

import json

import inspect

import asyncio

import importlib.util

from pathlib import Path

from typing import Dict, List, Any, Optional

from datetime import datetime

from ..config.manager import ConfigManager

from ..config.schema import DataType

from ..utils.data_transformer import DataTransformer

from ..utils.http_client import HTTPClient

from ..utils.html_extractor import HTMLExtractor

from ..ai_analyzer.api_finder import APIFinder

from ..ai_tools.response_validator import ResponseValidator

class AgentTools:

    """Tools available to AI agent for interactive scraping"""

    def __init__(self,
                     config_manager: ConfigManager,
                     proxies: Optional[Dict] = None,
                     enable_logging: bool = True):

        """

        Initialize agent tools.

        Args:

            config_manager: ConfigManager instance

            proxies: Optional proxy configuration

            enable_logging: Enable/disable logging

        """

        self.config_manager = config_manager

        self.http_client = HTTPClient(proxies)

        self.html_extractor = HTMLExtractor()

        self.data_transformer = DataTransformer()

        self.enable_logging = enable_logging

    def _log(self, level: str, message: str):

        """Centralized logging method."""

        if self.enable_logging:

            prefix = f"[{level}]" if level else ""

            print(f"{prefix} {message}")

    def get_available_actions(self) -> Dict[str, List[str]]:

        """

        Dynamically collect all available action methods.

        Returns:

            Dict with 'base_actions' and 'config_specific_actions'

        """

        # Get base actions from DataTransformer

        base_actions = []

        for name, method in inspect.getmembers(self.data_transformer, predicate=inspect.ismethod):

            if not name.startswith('_'):  # Skip private methods

                base_actions.append(name)

        # Get config-specific actions from all utils files

        config_specific = {}

        utils_dir = self.config_manager.utils_dir

        if utils_dir.exists():

            for utils_file in utils_dir.glob("*_utils.py"):

                config_name = utils_file.stem.replace('_utils', '')

                # Load the module to inspect its methods

                utils_module = self.config_manager.load_utils_module(config_name)

                if utils_module:

                    methods = []

                    for name, obj in inspect.getmembers(utils_module):

                        if callable(obj) and not name.startswith('_'):

                            methods.append(name)

                    if methods:

                        config_specific[config_name] = methods

        return {

            "base_actions": sorted(base_actions),

            "config_specific_actions": config_specific

        }

    def get_available_actions_formatted(self) -> str:

        """

        Get formatted string of all available actions for prompt.

        Returns:

            Formatted string for AI prompt

        """

        actions = self.get_available_actions()

        output = "## AVAILABLE ACTION METHODS\n\n"

        output += "### Base Actions (available for all configs):\n"

        for action in actions["base_actions"]:

            # Try to get docstring

            method = getattr(self.data_transformer, action, None)

            if method and method.__doc__:

                doc = method.__doc__.strip().split('\n')[0]  # First line only

                output += f"- {action}: {doc}\n"

            else:

                output += f"- {action}\n"

        if actions["config_specific_actions"]:

            output += "\n### Config-Specific Actions:\n"

            for config_name, methods in actions["config_specific_actions"].items():

                output += f"\n**{config_name}**:\n"

                for method in methods:

                    output += f"- {method}\n"

        return output

    # Tool 1: List configs

    def list_configs(self) -> List[str]:

        """

        Get all available configuration names.

        **Parameters**: None (no arguments required)

        **Returns**: List of config name strings

        **Example**:

            Result: ["bitcoin_stats", "ethereum_price", "hive_tps"]

        """

        self._log("Tool", "[list_configs] Called")

        configs = self.config_manager.list_config_names()

        self._log("Tool", f"[list_configs] Found {len(configs)} config(s): {configs}")

        return configs

    # Tool 2: Read config

    def read_config(self, config_name: str) -> Optional[Dict]:

        """

        Read an existing configuration file.

        **Parameters**:

            - `config_name` (str): Name of config file (without .json extension)

              - Format: Simple string, e.g., "bitcoin_stats", "ethereum_price"

              - Must match existing config filename

        **Returns**:

            - Dict with config structure: `{"metadata": {...}, "entities": {...}}`

            - None if config not found

        **Example**:

            Input: config_name="hive_tps"

            Output: {

                "metadata": {"data_type": "list", ...},

                "entities": {"hive": [{"name": "tps", "resources": [...]}]}

            }

        """

        return self.config_manager.load_config_dict(config_name)

    # Tool 3: Search configs with regex

    def search_configs_with_regex(self, pattern: str) -> Dict[str, List[str]]:

        """

        Search config files using regex pattern to find similar configurations.

        **Parameters**:

            - `pattern` (str): Regular expression pattern (Python regex syntax)

              - Examples: "api.*transaction", "blockchain.*tps", "price.*usd"

              - Case-insensitive matching

        **Returns**:

            - Dict: `{"config_file.json": ["Line 5: ...", "Line 12: ..."]}`

            - Keys are config filenames, values are lists of matching lines

        **Example**:

            Input: pattern="api.*statistics"

            Output: {

                "hive_tps.json": ["Line 23: url: https://api.example.com/statistics"],

                "bitcoin_stats.json": ["Line 15: api_path: statistics.count"]

            }

        """

        results = {}

        configs_dir = self.config_manager.configs_dir

        if not configs_dir.exists():

            return results

        regex = re.compile(pattern, re.IGNORECASE)

        for config_file in configs_dir.glob("*.json"):

            matches = []

            try:

                with open(config_file, 'r') as f:

                    for line_num, line in enumerate(f, 1):

                        if regex.search(line):

                            matches.append(f"Line {line_num}: {line.strip()}")

                if matches:

                    results[config_file.name] = matches

            except Exception as e:

                results[config_file.name] = [f"Error reading file: {e}"]

        return results

    def _validate_url(self, url: str) -> bool:

        """Validate URL format."""

        if not url:

            return False

        url = url.strip()

        return url.startswith(("http://", "https://")) and "." in url.split("://")[-1].split("/")[0]

    def _reduce_large_response(self, data: Any, max_items: int = 10) -> Any:

        """

        Intelligently reduce large responses by taking first 5 and last 5 items from lists.

        Only reduces if total response is > 500 chars.

        Args:

            data: Response data (dict, list, or any type)

            max_items: Maximum items to keep in lists (default: 10 = 5 first + 5 last)

        Returns:

            Reduced data structure (keeps original structure, just reduces large lists)

        """

        # First check total size

        try:

            total_size = len(json.dumps(data, default=str))

            if total_size <= 500:

                return data

        except:

            # If JSON serialization fails, return as-is

            return data

        def _reduce_recursive(obj: Any, depth: int = 0) -> Any:

            """Recursively reduce lists and dicts."""

            if depth > 5:  # Prevent infinite recursion

                return obj

            if isinstance(obj, list):

                # If list has more than max_items, take first 5 and last 5

                if len(obj) > max_items:

                    first_count = max_items // 2  # 5

                    last_count = max_items // 2   # 5

                    first_items = [_reduce_recursive(item, depth + 1) for item in obj[:first_count]]

                    last_items = [_reduce_recursive(item, depth + 1) for item in obj[-last_count:]]

                    # Return as list with indicator comment as last item

                    reduced_list = first_items + last_items

                    # Add a marker item at the end to indicate reduction

                    reduced_list.append({

                        "_reduction_info": True,

                        "_original_count": len(obj),

                        "_showing_first": first_count,

                        "_showing_last": last_count,

                        "_message": f"... ({len(obj) - max_items} items hidden) ..."

                    })

                    return reduced_list

                else:

                    # Recursively process items in smaller lists

                    return [_reduce_recursive(item, depth + 1) for item in obj]

            elif isinstance(obj, dict):

                # Recursively process dict values, remove metadata keys

                reduced_dict = {}

                metadata_keys = (
                    ["status_code", "headers", "url", "error", "content_type", "is_json", "rendered", "statusCode", "request", "response"])  # noqa: C0301

                for key, value in obj.items():

                    # Skip metadata keys - only keep actual content/body

                    if key.lower() in [k.lower() for k in metadata_keys]:

                        continue

                    reduced_dict[key] = _reduce_recursive(value, depth + 1)

                return reduced_dict

            else:

                # Primitive types, return as-is

                return obj

        return _reduce_recursive(data)

    # Tool 4: Fetch URL content

    async def fetch_url_content(self, url: str, render_js: bool = False, is_truncate=True) -> Dict[str, Any]:

        """

        Fetch content from URL with automatic JavaScript rendering detection.

        **Parameters**:

            - `url` (str): **REQUIRED** - Full URL with protocol

              - Format: Must start with `http://` or `https://`

              - Examples:

                - ✅ "https://api.example.com/data"

                - ✅ "http://example.com/page"

                - ❌ "api.example.com/data" (missing protocol)

                - ❌ "/api/data" (relative path)

            - `render_js` (bool, optional): Force JavaScript rendering (default: False)

              - Usually not needed - auto-detects if rendering required

        **Returns**:

            Dict with keys:

            - `url`: Original URL

            - `content`: Response content (dict for JSON, str for HTML)

            - `content_type`: MIME type (e.g., "application/json", "text/html")

            - `is_json`: Boolean indicating if content is JSON

            - `rendered`: Boolean indicating if Playwright was used

            - `status_code`: HTTP status code

            - `error`: Error message if request failed

        **Example**:

            Input: url="https://hbt5.hive.blog/hafbe-api/transaction-statistics?granularity=daily"

            Output: {

                "url": "https://...",

                "content": {"data": [{"date": "2024-01-01", "count": 1000}]},

                "content_type": "application/json",

                "is_json": True,

                "rendered": False,

                "status_code": 200,

                "error": None

            }

        """

        self._log("Tool", f"[fetch_url_content] URL: {url}, render_js: {render_js}")

        # Validate URL first

        if not self._validate_url(url):

            error_msg = f"Invalid URL format: '{url}'. URL must start with http:// or https://"

            self._log("Tool", f"[fetch_url_content] ✗ {error_msg}")

            return {

                "url": url,

                "content": None,

                "content_type": None,

                "is_json": False,

                "error": error_msg

            }

        result = {

            "url": url,

            "content": None,

            "content_type": None,

            "is_json": False,

            "error": None

        }

        try:

            self._log("Tool", f"[fetch_url_content] Fetching content with smart rendering...")

            # Use smart fetching (auto-detects if rendering is needed)

            fetch_result = await self.http_client.fetch_content_smart(url)

            # Store original for logging

            original_content = fetch_result.get("content")

            # Intelligently reduce large responses (only content/body)

            if original_content is not None:

                # For JSON content, reduce large lists/dicts

                if fetch_result.get("is_json"):
                    if is_truncate:
                        reduced_content = self._reduce_large_response(original_content)

                        result["content"] = reduced_content

                    # Log reduction if it happened

                    def _has_reduction_info(obj: Any) -> bool:

                        """Check if object contains reduction info."""

                        if isinstance(obj, list):

                            return any(isinstance(item,
                            dict) and item.get("_reduction_info") for item in obj)

                        elif isinstance(obj, dict):

                            return any(_has_reduction_info(v) for v in obj.values())

                        return False

                    if _has_reduction_info(reduced_content):

                        self._log("Tool",
                        f"[fetch_url_content] Large lists detected: showing first 5 + last 5 items (content reduced)")

                else:

                    # For HTML, keep as-is but truncate if extremely long

                    content = original_content

                    if isinstance(content, str) and len(content) > 10000 and is_truncate:
                        result["content"] = content[:10000] + "... (truncated)"

                    else:

                        result["content"] = content

            else:

                result["content"] = None

            # Copy other metadata

            result["content_type"] = fetch_result.get("content_type")

            result["is_json"] = fetch_result.get("is_json", False)

            result["rendered"] = fetch_result.get("rendered", False)

            result["status_code"] = fetch_result.get("status_code")

            # Log results

            if fetch_result.get("rendered"):

                self._log("Tool", f"[fetch_url_content] ✓ Content rendered with Playwright")

            if fetch_result.get("is_json"):

                self._log("Tool", f"[fetch_url_content] ✓ JSON response received")

                if isinstance(result.get("content"), dict):

                    keys = [k for k in result["content"].keys() if not k.startswith("_")]

                    self._log("Tool", f"[fetch_url_content] JSON keys: {keys[:10]}")

            content_size = len(json.dumps(result.get("content", "")))

            self._log("Tool", f"[fetch_url_content] ✓ Content processed ({content_size} chars)")

            if fetch_result.get("error"):

                result["error"] = fetch_result["error"]

                self._log("Tool", f"[fetch_url_content] ⚠ {fetch_result['error']}")

        except Exception as e:

            error_msg = str(e)

            self._log("Tool", f"[fetch_url_content] ✗ Exception: {error_msg}")

            result["error"] = error_msg

        return result

    # Tool 5: Discover APIs

    async def discover_apis(self, url: str,
    search_keywords: Optional[List[str]] = None) -> Dict[str, Any]:

        """

        Automatically discover API endpoints from web page using browser interception.

        Loads the page with Playwright and captures all network API calls.

        **Parameters**:

            - `url` (str): **REQUIRED** - Full URL with protocol

              - Format: Must start with `http://` or `https://`

              - Examples:

                - ✅ "https://example.com/dashboard"

                - ✅ "http://app.example.com/data"

            - `search_keywords` (List[str], optional): Keywords to filter API responses

              - Examples: ["transaction", "statistics", "api", "data"]

              - If provided, only returns APIs whose responses contain these keywords

        **Returns**:

            Dict with keys:

            - `success`: Boolean indicating if discovery succeeded

            - `total_apis`: Total number of APIs discovered

            - `matched_apis`: List of APIs matching keywords (if provided)

              - Each API: `{"url": "...", "method": "GET", "matched_keywords": [...]}`

            - `all_apis`: List of all discovered APIs

            - `error`: Error message if failed

        **Example**:

            Input:

                url="https://example.com/dashboard"

                search_keywords=["transaction", "stats"]

            Output: {

                "success": True,

                "total_apis": 15,

                "matched_apis": [

                    {

                        "url": "https://api.example.com/transactions",

                        "method": "GET",

                        "matched_keywords": ["transaction"]

                    }

                ],

                "all_apis": [...]

            }

        """

        self._log("Tool", f"[discover_apis] URL: {url}, Keywords: {search_keywords}")

        try:

            # Use API finder with browser-based discovery (30 second timeout)

            finder = APIFinder(url)

            result = await finder.find_apis(url, search_keywords, timeout_seconds=30.0)

            self._log("Tool", f"[discover_apis] Found {result.get('total_apis', 0)} API calls")

            # Log matched APIs if any

            matched = result.get('matched_apis', [])

            if matched:

                self._log("Tool", f"[discover_apis] Matched {len(matched)} APIs with keywords")

                for api in matched[:3]:  # Show first 3

                    self._log("Tool",
                    f"[discover_apis]   ✓ {api['url']} - {api.get('matched_keywords', [])}")

            return result

        except Exception as e:

            self._log("Tool", f"[discover_apis] ✗ Error: {e}")

            return {

                "success": False,

                "error": str(e),

                "total_apis": 0,

                "matched_apis": [],

                "all_apis": []

            }

    # Tool 6: Test XPath on HTML

    async def test_xpath_on_html(self, url: str, xpath: str) -> Dict[str, Any]:

        """

        Test XPath expression on HTML content from URL. Fetches content internally.

        **Parameters**:

            - `url` (str): **REQUIRED** - Full URL to fetch HTML content from

              - Format: Must start with `http://` or `https://`

              - Tool will automatically fetch and render if needed

            - `xpath` (str): **REQUIRED** - XPath expression (standard XPath 1.0 syntax)

              - Examples:

                - `"//div[@class='price']"` - Find div with class="price"

                - `"//span[@id='count']"` - Find span with id="count"

                - `"//div[@class='price']/text()"` - Get text content

                - `"//table//tr[1]//td[2]"` - First row, second column

                - `"//div[contains(@class, 'metric')]"` - Div containing "metric" in class

        **Returns**:

            Dict with keys:

            - `url`: The URL tested

            - `xpath`: The XPath expression tested

            - `extracted_value`: Extracted value (string/list/None)

            - `success`: Boolean indicating if value was found

            - `error`: Error message if fetch failed or XPath is invalid

        **Example**:

            Input:

                url="https://example.com/page"

                xpath="//div[@class='price']/text()"

            Output: {

                "url": "https://example.com/page",

                "xpath": "//div[@class='price']/text()",

                "extracted_value": "$100",

                "success": True,

                "error": None

            }

        """

        result = {

            "url": url,

            "xpath": xpath,

            "extracted_value": None,

            "success": False,

            "error": None

        }

        try:

            # Fetch content first

            self._log("Tool", f"[test_xpath_on_html] Fetching content from: {url}")

            fetch_result = await self.http_client.fetch_content_smart(url)

            if fetch_result.get("error"):

                result["error"] = f"Failed to fetch URL: {fetch_result['error']}"

                return result

            html_content = fetch_result.get("content")

            if not html_content:

                result["error"] = "No HTML content received from URL"

                return result

            # Test XPath on fetched content

            self._log("Tool", f"[test_xpath_on_html] Testing XPath: {xpath}")

            value = self.html_extractor.extract_with_xpath(html_content, xpath)

            result["extracted_value"] = value

            result["success"] = value is not None

            if result["success"]:

                self._log("Tool", f"[test_xpath_on_html] ✓ Extracted value: {value}")

            else:

                self._log("Tool",
                f"[test_xpath_on_html] ✗ XPath '{xpath}' returned None (not found)")

        except Exception as e:

            error_msg = str(e)

            self._log("Tool", f"[test_xpath_on_html] ✗ Error: {error_msg}")

            result["error"] = error_msg

        return result

    # Tool 7: Test API path on JSON

    async def test_api_path_on_json(self, url: str, path: str) -> Dict[str, Any]:

        """

        Test JSON path (deep access) on JSON data from URL. Fetches content internally.

        **Parameters**:

            - `url` (str): **REQUIRED** - Full URL to fetch JSON content from

              - Format: Must start with `http://` or `https://`

              - Tool will automatically fetch JSON response

            - `path` (str): **REQUIRED** - Dot-notation JSON path with special keywords

              **UNDERSTANDING JSON STRUCTURE:**

              The API response can be:

              1. **Direct object** (dict): `{"trx_count": 100, "date": "2024-01-01"}`

              2. **Array of objects** (list): `[{"trx_count": 100}, {"trx_count": 200}]`

              3. **Nested structure**: `{"data": {"items": [{"count": 50}]}}`

              **PATH CONSTRUCTION RULES:**

              **Case 1: API returns a DIRECT OBJECT (dict)**

              - Path: Direct field name

              - Examples: `"trx_count"`, `"date"`, `"avg_trx"`

              - Access: `data["trx_count"]`

              **Case 2: API returns an ARRAY OF OBJECTS (list)**

              - Path: MUST start with list navigation keyword, then field name

              - Examples:

                - `"last.trx_count"` - Get trx_count from last item

                - `"first.trx_count"` - Get trx_count from first item

                - `"second.date"` - Get date from second item

                - `"second_last.avg_trx"` - Get avg_trx from second-to-last item

              - Access: `data[-1]["trx_count"]` (for last), `data[0]["trx_count"]` (for first)

              **Case 3: API returns NESTED STRUCTURE**

              - Path: Navigate through nested keys, then list navigation (if needed), then field

              - Examples:

                - `"data.transactions.last.trx_count"` - Navigate to data.transactions (list),
                get last, then trx_count

                - `"response.items.first.value"` - Navigate to response.items (list), get first,
                then value

              - Access: `data["data"]["transactions"][-1]["trx_count"]`

              **ALL AVAILABLE PATH KEYWORDS:**

              **For Lists (Arrays):**

              - `first` - First item (index 0)

              - `last` - Last item (index -1)

              - `second` - Second item (index 1)

              - `second_last` - Second-to-last item (index -2)

              - `length` - Length of list (returns number)

              - `reverse` - Reverse the list

              - `sort.key.order` - Sort list by key (order: "asc" or "desc")

              - `filter.date_key.days` - Filter list by date (e.g., `filter.date.1` = yesterday)

              - `[numeric_index]` - Access by numeric index (e.g., `0`, `1`, `-1`)

              **For Dictionaries (Objects):**

              - `key_name` - Access by key name directly (e.g., `trx_count`, `date`)

              - `value` - Get value of first key in dict

              - `kvalue` - Get value of "value" key specifically

              **Recursive Chaining:**

              - You can chain any of these: `data.transactions.last.trx_count`

              - Order: Navigate dicts → Navigate lists → Access fields

              **COMMON PATTERNS:**

              1. **Array response, need latest value:**

                 - Response: `[{"trx_count": 100}, {"trx_count": 200}]`

                 - Path: `"last.trx_count"` → Returns `200`

              2. **Array response, need first value:**

                 - Response: `[{"date": "2024-01-01"}, {"date": "2024-01-02"}]`

                 - Path: `"first.date"` → Returns `"2024-01-01"`

              3. **Direct object response:**

                 - Response: `{"trx_count": 393604, "date": "2025-11-02"}`

                 - Path: `"trx_count"` → Returns `393604`

              4. **Nested structure:**

                 - Response: `{"data": {"stats": [{"count": 100}]}}`

                 - Path: `"data.stats.first.count"` → Returns `100`

              **CRITICAL RULES:**

              - If response is a **list**, you MUST use `first.`, `last.`, etc. before field name

              - If response is a **dict**, use field name directly

              - Always check the structure first with `fetch_url_content` before constructing path

        **Returns**:

            Dict with keys:

            - `url`: The URL tested

            - `path`: The JSON path tested

            - `extracted_value`: Extracted value (any type/None)

            - `success`: Boolean indicating if value was found

            - `error`: Error message if fetch failed or path is invalid

        **Examples**:

            1. Array response, get latest transaction count:

               Input: url="https://api.example.com/stats", path="last.trx_count"

               Output: {"extracted_value": 393604, "success": True}

            2. Direct object response:

               Input: url="https://api.example.com/data", path="trx_count"

               Output: {"extracted_value": 393604, "success": True}

            3. Nested structure:

               Input: url="https://api.example.com/data", path="data.transactions.last.count"

               Output: {"extracted_value": 200, "success": True}

        """

        self._log("Tool", f"[test_api_path_on_json] Testing path: '{path}' on URL: {url}")

        result = {

            "url": url,

            "path": path,

            "extracted_value": None,

            "success": False,

            "error": None

        }

        try:

            # Fetch content first

            self._log("Tool", f"[test_api_path_on_json] Fetching content from: {url}")

            fetch_result = await self.http_client.fetch_content_smart(url)

            if fetch_result.get("error"):

                result["error"] = f"Failed to fetch URL: {fetch_result['error']}"

                return result

            if not fetch_result.get("is_json"):

                result["error"] = "URL did not return JSON content"

                return result

            json_data = fetch_result.get("content")

            if not json_data:

                result["error"] = "No JSON content received from URL"

                return result

            # Parse if string

            if isinstance(json_data, str):

                try:

                    json_data = json.loads(json_data)

                except Exception as e:

                    result["error"] = f"Invalid JSON: {str(e)}"

                    return result

            # Log JSON structure

            if isinstance(json_data, dict):

                self._log("Tool",
                f"[test_api_path_on_json] JSON has keys: {list(json_data.keys())[:10]}")

            # Test path

            value = self.data_transformer.extract_from_json_path(json_data, path)

            result["extracted_value"] = value

            result["success"] = value is not None

            if result["success"]:

                self._log("Tool",
                f"[test_api_path_on_json] ✓ Extracted value: {value} (type: {type(value).__name__})")

            else:

                self._log("Tool",
                f"[test_api_path_on_json] ✗ Path '{path}' returned None (not found)")

        except Exception as e:

            error_msg = str(e)

            self._log("Tool", f"[test_api_path_on_json] ✗ Error: {error_msg}")

            result["error"] = error_msg

        return result

    # Tool 8: Get method implementation

    def get_method_implementation(self,
                                      method_name: str,
                                      config_name: Optional[str] = None) -> Dict[str, Any]:

        """

        Get source code and documentation of an action method.

        **Parameters**:

            - `method_name` (str): **REQUIRED** - Name of the method

              - Examples: "extract_numeric_value", "calculate_tps_from_transactions"

              - Must match existing method name (case-sensitive)

            - `config_name` (str, optional): Name of config for config-specific methods

              - Only needed if method is in config-specific utils (not base utils)

              - Examples: "bitcoin_stats", "hive_tps"

              - If None, searches in base utils first

        **Returns**:

            Dict with keys:

            - `method_name`: Name of method

            - `source`: Python source code (full function definition)

            - `docstring`: Method documentation string

            - `location`: Where method is located ("base:DataTransformer" or "config_specific:config_name")

            - `error`: Error message if method not found

        **Example**:

            Input:

                method_name="extract_numeric_value"

                config_name=None

            Output: {

                "method_name": "extract_numeric_value",

                "source": "def extract_numeric_value(value):\\n    ...",

                "docstring": "Extract numeric value from string...",

                "location": "base:DataTransformer",

                "error": None

            }

        """

        result = {

            "method_name": method_name,

            "source": None,

            "docstring": None,

            "location": None,

            "error": None

        }

        try:

            method = None

            # Check config-specific utils first

            if config_name:

                utils_module = self.config_manager.load_utils_module(config_name)

                if utils_module and hasattr(utils_module, method_name):

                    method = getattr(utils_module, method_name)

                    result["location"] = f"config_specific:{config_name}"

            # Check base transformer

            if not method and hasattr(self.data_transformer, method_name):

                method = getattr(self.data_transformer, method_name)

                result["location"] = "base:DataTransformer"

            if method:

                result["source"] = inspect.getsource(method)

                result["docstring"] = inspect.getdoc(method)

            else:

                result["error"] = f"Method '{method_name}' not found"

        except Exception as e:

            result["error"] = str(e)

        return result

    # Tool 9: Write custom method

    def write_custom_method(

        self,

        method_name: str,

        method_code: str,

        config_name: Optional[str] = None,

        add_to_base_utils: bool = False

    ) -> Dict[str, Any]:

        """

        Write a new custom action method to utils file.

        **Parameters**:

            - `method_name` (str): **REQUIRED** - Name of new method (must be valid Python identifier)

              - Examples: "calculate_difficulty", "parse_transaction_data"

            - `method_code` (str): **REQUIRED** - Complete Python function code

              - Must include full function definition: `def method_name(args): ...`

              - Should include docstring

              - Example:

                ```python

                def calculate_tps(transactions, seconds):

                    \"\"\"Calculate transactions per second.\"\"\"

                    return transactions / seconds if seconds > 0 else 0

                ```

            - `config_name` (str, optional): Config name for config-specific utils

              - If provided, method goes to `.scrapai/utils/{config_name}_utils.py`

              - Example: "bitcoin_stats"

              - Cannot be used with `add_to_base_utils=True`

            - `add_to_base_utils` (bool, optional): If True, add to user's base_utils.py

              - Shared across all configs

              - File: `.scrapai/utils/base_utils.py`

              - Cannot be used with `config_name`

        **Returns**:

            Dict with keys:

            - `method_name`: Name of method

            - `success`: Boolean indicating if write succeeded

            - `file_path`: Path to utils file where method was written

            - `location`: Location type ("user_base_utils" or "config:{config_name}")

            - `error`: Error message if write failed

        **Example**:

            Input:

                method_name="calculate_tps"

                method_code="def calculate_tps(count, seconds): return count / seconds"

                config_name="hive_tps"

            Output: {

                "method_name": "calculate_tps",

                "success": True,

                "file_path": "/path/to/.scrapai/utils/hive_tps_utils.py",

                "location": "config:hive_tps",

                "error": None

            }

        """

        result = {

            "method_name": method_name,

            "success": False,

            "error": None,

            "file_path": None,

            "location": None

        }

        try:

            if add_to_base_utils:

                # Add to user's shared base_utils.py

                utils_path = self.config_manager.utils_dir / "base_utils.py"

                result["location"] = "user_base_utils"

            elif config_name:

                # Add to config-specific utils

                utils_path = self.config_manager.utils_dir / f"{config_name}_utils.py"

                result["location"] = f"config:{config_name}"

            else:

                result["error"] = "Must specify either config_name or add_to_base_utils=True"

                return result

            # Read existing content or create new

            if utils_path.exists():

                with open(utils_path, 'r') as f:

                    existing_code = f.read()

            else:

                if add_to_base_utils:

                    existing_code = '"""\nUser-specific base utilities.\n\nShared utility functions that can be reused across multiple configs.\n"""\n\n'  # noqa: C0301

                else:

                    existing_code = f'"""\nCustom utility methods for {config_name}\n"""\n\n'

            # Append new method

            new_code = existing_code + "\n\n" + method_code + "\n"

            # Write back

            with open(utils_path, 'w') as f:

                f.write(new_code)

            result["success"] = True

            result["file_path"] = str(utils_path)

        except Exception as e:

            result["error"] = str(e)

        return result

    # Tool 10: Run config test

    async def run_config_test(self, config_name: str) -> Dict[str, Any]:

        """

        Execute a configuration to test if it works and extract sample data.

        **Parameters**:

            - `config_name` (str): **REQUIRED** - Name of config to test

              - Format: Simple string, e.g., "bitcoin_stats", "hive_tps"

              - Must match existing config filename (without .json)

        **Returns**:

            Dict with keys:

            - `config_name`: Name of config tested

            - `success`: Boolean indicating if extraction succeeded

            - `data`: Extracted data (dict/list/None)

            - `errors`: List of error info dicts

            - `resources_tried`: Number of resources attempted

            - `resources_succeeded`: Number of resources that succeeded

            - `execution_time_seconds`: Time taken to execute

        **Example**:

            Input: config_name="hive_tps"

            Output: {

                "config_name": "hive_tps",

                "success": True,

                "data": {"tps": 1234.5},

                "errors": [],

                "resources_tried": 1,

                "resources_succeeded": 1,

                "execution_time_seconds": 0.5

            }

        """

        # This would use the execution engine

        # For now, return a placeholder

        return {

            "config_name": config_name,

            "note": "Execution requires ExecutionEngine - integrate in agent"

        }

    # Tool 11: Validate results

    def validate_results(self, data: Any, expected_type: str, description: str) -> Dict[str, Any]:

        """

        Validate extracted data matches expected format and type.

        **Parameters**:

            - `data` (Any): **REQUIRED** - Extracted data to validate

              - Can be any Python type: str, int, float, dict, list, None

              - Example: `1000`, `"Bitcoin"`, `[1, 2, 3]`, `{"name": "value"}`

            - `expected_type` (str): **REQUIRED** - Expected data type

              - Options: `"single_value"`, `"list"`, `"object"`

              - Examples:

                - `"single_value"` - Single number or string

                - `"list"` - Array/list of items

                - `"object"` - Dictionary/object with key-value pairs

            - `description` (str): **REQUIRED** - Description of what data represents

              - Examples: "Transaction count", "List of prices", "User profile object"

              - Used for validation context and error messages

        **Returns**:

            Dict with keys:

            - `is_valid`: Boolean indicating if data matches expected type

            - `actual_type`: Detected type of data ("single_value", "list", "object", "null")

            - `issues`: List of validation issues (if any)

            - `warnings`: List of warnings (non-critical issues)

        **Example**:

            Input:

                data=1234

                expected_type="single_value"

                description="Transaction count"

            Output: {

                "is_valid": True,

                "actual_type": "single_value",

                "issues": [],

                "warnings": []

            }

        """

        validator = ResponseValidator()

        # Convert string to DataType

        try:

            data_type = DataType(expected_type)

        except:

            data_type = DataType.SINGLE_VALUE

        return validator.validate_response(data, data_type, description)

    # Tool 12: Update brain file

    def update_brain(self, content: str, brain_type: str = "ai_analyzer") -> Dict[str, Any]:

        """

        Add new knowledge/rules to brain files for future reference.

        **Parameters**:

            - `content` (str): **REQUIRED** - Knowledge content to add

              - Format: Plain text or markdown

              - Examples: "API endpoints at /api/* usually return JSON",
              "Use xpath //div[@class='metric'] for metrics"

              - Will be appended with timestamp

            - `brain_type` (str, optional): Type of brain file (default: "ai_analyzer")

              - Options: `"ai_analyzer"` or `"project"`

              - `"ai_analyzer"`: Rules for AI analyzer (stored in `.brain.ai_analyzer`)

              - `"project"`: Project-specific knowledge (stored in `.brain`)

        **Returns**:

            Dict with keys:

            - `brain_type`: Type of brain file updated

            - `success`: Boolean indicating if update succeeded

            - `message`: Success message

            - `error`: Error message if update failed

        **Example**:

            Input:

                content="Hive blockchain APIs use /hafbe-api/ prefix"

                brain_type="ai_analyzer"

            Output: {

                "brain_type": "ai_analyzer",

                "success": True,

                "message": "Brain updated: .brain.ai_analyzer",

                "error": None

            }

        """

        result = {

            "brain_type": brain_type,

            "success": False,

            "error": None

        }

        try:

            brain_file = ".brain" if brain_type == "project" else ".brain.ai_analyzer"

            # Brain files go in .scrapai folder

            brain_path = self.config_manager.scrapai_dir / brain_file

            if not brain_path.exists():

                result["error"] = f"Brain file not found: {brain_file}"

                return result

            # Read existing content

            with open(brain_path, 'r') as f:

                existing = f.read()

            # Append new knowledge

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            new_entry = f"\n\n## Updated: {timestamp}\n{content}\n"

            updated = existing + new_entry

            # Write back

            with open(brain_path, 'w') as f:

                f.write(updated)

            result["success"] = True

            result["message"] = f"Brain updated: {brain_file}"

        except Exception as e:

            result["error"] = str(e)

        return result

    # Tool 13: Read existing config to learn

    def read_existing_config(self, config_name: str) -> Dict[str, Any]:

        """

        Read an existing config to learn patterns, structure, and best practices.

        **Parameters**:

            - `config_name` (str): **REQUIRED** - Name of existing config to learn from

              - Format: Simple string, e.g., "bitcoin_stats", "hive_tps"

              - Must match existing config filename (without .json)

        **Returns**:

            Dict with keys:

            - `config_name`: Name of config

            - `exists`: Boolean indicating if config exists

            - `config`: Full config dictionary

            - `analysis`: Analysis breakdown with:

              - `num_entities`: Number of entities in config

              - `entities`: List of entity names

              - `total_metrics`: Total number of metrics

              - `metadata`: Config metadata

              - `resource_types_used`: List of resource types used

              - `actions_used`: List of action methods used

            - `error`: Error message if config not found

        **Example**:

            Input: config_name="hive_tps"

            Output: {

                "config_name": "hive_tps",

                "exists": True,

                "config": {...},

                "analysis": {

                    "num_entities": 1,

                    "entities": ["hive"],

                    "total_metrics": 1,

                    "resource_types_used": ["api"],

                    "actions_used": ["calculate_tps_from_transactions"]

                },

                "error": None

            }

        """

        result = {

            "config_name": config_name,

            "exists": False,

            "config": None,

            "analysis": {},

            "error": None

        }

        try:

            config_dict = self.config_manager.load_config_dict(config_name)

            if not config_dict:

                result["error"] = "Config not found"

                return result

            result["exists"] = True

            result["config"] = config_dict

            # Analyze structure

            entities = config_dict.get("entities", {})

            result["analysis"] = {

                "num_entities": len(entities),

                "entities": list(entities.keys()),

                "total_metrics": sum(len(metrics) for metrics in entities.values()),

                "metadata": config_dict.get("metadata", {}),

                "resource_types_used": self._analyze_resource_types(entities),

                "actions_used": self._analyze_actions_used(entities)

            }

            return result

        except Exception as e:

            result["error"] = str(e)

            return result

    def _analyze_resource_types(self, entities: Dict) -> List[str]:

        """Extract unique resource types from config."""

        types = set()

        for metrics_list in entities.values():

            for metric in metrics_list:

                for resource in metric.get("resources", []):

                    types.add(resource.get("resource_type", "unknown"))

        return list(types)

    def _analyze_actions_used(self, entities: Dict) -> List[str]:

        """Extract all unique action methods from config."""

        actions = set()

        for metrics_list in entities.values():

            for metric in metrics_list:

                for resource in metric.get("resources", []):

                    actions.update(resource.get("actions_methods", []))

                    actions.update(resource.get("pre_actions_methods", []))

                    actions.update(resource.get("extra_actions", []))

        return list(actions)

    # Tool 14: List user's base_utils methods

    def list_user_base_utils_methods(self) -> Dict[str, Any]:

        """

        List all methods available in user's shared base_utils.py file.

        **Parameters**: None (no arguments required)

        **Returns**:

            Dict with keys:

            - `exists`: Boolean indicating if base_utils.py exists

            - `methods`: List of method info dicts, each with:

              - `name`: Method name

              - `signature`: Full method signature (e.g., "calculate_tps(count, seconds)")

              - `docstring`: Method documentation

            - `error`: Error message if file not found or read failed

        **Example**:

            Output: {

                "exists": True,

                "methods": [

                    {

                        "name": "calculate_tps",

                        "signature": "calculate_tps(count: int, seconds: float)",

                        "docstring": "Calculate transactions per second"

                    },

                    {

                        "name": "format_price",

                        "signature": "format_price(value: str)",

                        "docstring": "Format price string to number"

                    }

                ],

                "error": None

            }

        """

        result = {

            "exists": False,

            "methods": [],

            "error": None

        }

        try:

            base_utils_path = self.config_manager.utils_dir / "base_utils.py"

            if not base_utils_path.exists():

                result["error"] = (
                    "User base_utils.py not found. Will be created when first custom method is added.")

                return result

            result["exists"] = True

            # Import and inspect

            spec = importlib.util.spec_from_file_location("user_base_utils", base_utils_path)

            module = importlib.util.module_from_spec(spec)

            spec.loader.exec_module(module)

            # Get all functions

            for name, obj in inspect.getmembers(module):

                if inspect.isfunction(obj) and not name.startswith('_'):

                    sig = str(inspect.signature(obj))

                    doc = inspect.getdoc(obj) or "No description"

                    result["methods"].append({

                        "name": name,

                        "signature": f"{name}{sig}",

                        "docstring": doc

                    })

            return result

        except Exception as e:

            result["error"] = str(e)

            return result

    # Tool 15: Add entity/metric to existing config

    def add_to_existing_config(

        self,

        config_name: str,

        entity_name: str,

        metric_name: str,

        resources: List[Dict]

    ) -> Dict[str, Any]:

        """

        Add a new entity or metric to an existing configuration file.

        **Parameters**:

            - `config_name` (str): **REQUIRED** - Name of existing config

              - Format: Simple string, e.g., "bitcoin_stats"

              - Config must already exist

            - `entity_name` (str): **REQUIRED** - Name of entity

              - Examples: "bitcoin", "ethereum", "hive", "user"

              - If entity doesn't exist, it will be created

            - `metric_name` (str): **REQUIRED** - Name of metric to add

              - Examples: "price", "tps", "transaction_count", "difficulty"

              - If metric exists, it will be updated (replaced)

            - `resources` (List[Dict]): **REQUIRED** - List of resource configurations

              - Each resource dict must have: `url`, `resource_type`, `api_path`/`xpath`/`path`

              - Format: `[{"url": "...", "resource_type": "api", "api_path": "...", ...}]`

              - Example:

                ```python

                [{

                    "url": "https://api.example.com/stats",

                    "resource_type": "api",

                    "api_path": "data.last.count",

                    "actions_methods": ["extract_numeric_value"]

                }]

                ```

        **Returns**:

            Dict with keys:

            - `config_name`: Name of config

            - `success`: Boolean indicating if update succeeded

            - `action`: Action taken ("created_entity", "added_metric", "updated_metric")

            - `error`: Error message if update failed

        **Example**:

            Input:

                config_name="bitcoin_stats"

                entity_name="bitcoin"

                metric_name="difficulty"

                resources=[{"url": "https://api.example.com/difficulty", "api_path": "difficulty"}]

            Output: {

                "config_name": "bitcoin_stats",

                "success": True,

                "action": "added_metric",

                "error": None

            }

        """

        result = {

            "config_name": config_name,

            "success": False,

            "action": None,  # "created_entity", "added_metric", "updated_metric"

            "error": None

        }

        try:

            # Load existing config

            config_dict = self.config_manager.load_config_dict(config_name)

            if not config_dict:

                result["error"] = "Config not found"

                return result

            # Ensure entities key exists

            if "entities" not in config_dict:

                config_dict["entities"] = {}

            entities = config_dict["entities"]

            # Check if entity exists

            if entity_name not in entities:

                # Create new entity

                entities[entity_name] = []

                result["action"] = "created_entity"

            # Check if metric exists in entity

            existing_metric = None

            for idx, metric in enumerate(entities[entity_name]):

                if metric.get("name") == metric_name:

                    existing_metric = idx

                    break

            if existing_metric is not None:

                # Update existing metric

                entities[entity_name][existing_metric]["resources"] = resources

                result["action"] = "updated_metric"

            else:

                # Add new metric

                entities[entity_name].append({

                    "name": metric_name,

                    "resources": resources

                })

                if result["action"] is None:

                    result["action"] = "added_metric"

            # Save updated config

            if self.config_manager.save_config_dict(config_name, config_dict):

                result["success"] = True

            else:

                result["error"] = "Failed to save config"

            return result

        except Exception as e:

            result["error"] = str(e)

            return result

    async def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """
        Execute a tool by name.

        This method handles tool execution for AI agent tool calls.
        It checks if the tool exists and handles both sync and async methods.

        Args:
            tool_name: Name of tool to execute
            tool_args: Arguments for the tool

        Returns:
            Tool result or error dict
        """
        tool_method = getattr(self, tool_name, None)

        if not tool_method:
            return {"error": f"Tool '{tool_name}' not found"}

        try:
            # Check if method is async
            if inspect.iscoroutinefunction(tool_method):
                return await tool_method(**tool_args)
            else:
                return tool_method(**tool_args)
        except Exception as e:
            return {"error": f"Error executing tool: {str(e)}"}
