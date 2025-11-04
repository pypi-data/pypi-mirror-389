"""
XML Parser and Syntax Handler - Complete XML processing for AI responses

Handles:
1. XML syntax validation and parsing (extracting structure from AI responses)
2. XML format prompt generation (for system prompts)
3. Config parsing (converting XML to configuration dictionaries)
4. XML building (formatting data as XML for AI consumption)

"""

import re
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..config.schema import (
    ScraperConfig, MetricConfig, ResourceConfig, ConfigMetadata,
    DataType, ResourceType
)


class XMLConfigParser:
    """
    Complete XML handler for AI responses and configuration parsing.
    
    Combines validation, syntax handling, and config parsing functionality.
    """

    # ============================================================================
    # XML FORMAT PROMPT GENERATION
    # ============================================================================

    @staticmethod
    def get_xml_format_prompt() -> str:
        """
        Get the XML format instructions to inject into system prompt at runtime.

        Returns:
            XML format instructions string
        """
        return """

## CRITICAL: RESPONSE FORMAT (MANDATORY)

**YOU MUST RESPOND ONLY IN XML FORMAT. NO EXCEPTIONS.**

**EVERY RESPONSE MUST FOLLOW THIS EXACT STRUCTURE:**

```xml
<xml>
  <message>Optional explanatory message if needed</message>
  <tool_calls>
    <tool_call>
      <name>tool_name</name>
      <args>...</args>
    </tool_call>
  </tool_calls>
  <scraper_config>
    <!-- Full config structure here -->
  </scraper_config>
  <status>done</status>
</xml>
```

**MANDATORY STRUCTURE:**

1. **ALWAYS start with `<xml>` and end with `</xml>`** - This is the root wrapper

2. **Inside `<xml>`, you can have (in any order):**
   - `<message>...</message>` - Optional explanatory text (only if needed)
   - `<tool_calls>...</tool_calls>` - Optional tool calls (only if needed)
   - `<scraper_config>...</scraper_config>` - Config structure (when creating configs)
   - `<status>done</status>` - Status indicator (use "done" when complete, "processing" if continuing)

3. **Rules:**
   - NO greetings, explanations, or markdown outside XML tags
   - NO markdown code blocks (```xml) - Only raw XML
   - NO text before `<xml>` or after `</xml>`
   - Response must START with `<xml>` and END with `</xml>`

**VALID EXAMPLES:**

Example 1: With tool calls
```xml
<xml>
  <message>I need to fetch the URL content first to analyze structure</message>
  <tool_calls>
    <tool_call>
      <name>fetch_url_content</name>
      <args>
        <url>https://api.example.com/data</url>
      </args>
    </tool_call>
  </tool_calls>
  <status>processing</status>
</xml>
```

Example 2: Final config with completion
```xml
<xml>
  <scraper_config>
    <name>example_config</name>
    <metadata>...</metadata>
    <entities>...</entities>
  </scraper_config>
  <status>done</status>
</xml>
```

Example 3: Error or clarification
```xml
<xml>
  <message>I need more information about what data to extract</message>
  <status>processing</status>
</xml>
```

**INVALID (DO NOT DO THIS):**

❌ Starting without `<xml>`:
```
<scraper_config>...</scraper_config>
```

❌ Missing closing `</xml>`:
```xml
<xml>
  <scraper_config>...</scraper_config>
```

❌ Plain text before/after:
```
Here's the config:
<xml>...</xml>
Done!
```

❌ Markdown code block:
```xml
<xml>...</xml>
```

❌ Missing status:
```xml
<xml>
  <scraper_config>...</scraper_config>
</xml>
```

**REMEMBER:**
- ALWAYS wrap everything in `<xml>...</xml>`
- ALWAYS include `<status>done</status>` or `<status>processing</status>`
- Inside `<xml>` you can have: `<message>`, `<tool_calls>`, `<scraper_config>`, `<status>`
"""

    # ============================================================================
    # XML VALIDATION AND PARSING
    # ============================================================================

    @staticmethod
    def validate_and_parse(ai_response: str) -> Dict[str, Any]:
        """
        Validate and parse AI response XML.

        Handles XML response formats:
        1. Standard format (REQUIRED): <xml><message>...</message><tool_calls>...</tool_calls><scraper_config>...</scraper_config><status>done</status></xml>
        2. Tool calls: <xml><tool_calls><tool_call>...</tool_call></tool_calls><status>processing</status></xml>
        3. Scraper config: <xml><scraper_config>...</scraper_config><status>done</status></xml>
        4. Multiple configs: <xml><scraper_config>...</scraper_config><scraper_config>...</scraper_config><status>done</status></xml>
        5. Backward compat: Direct <scraper_config> or <tool_call> without <xml> wrapper (deprecated)

        Args:
            ai_response: Raw AI response string

        Returns:
            Dictionary with:
            {
                "valid": bool,
                "error": Optional[str],
                "message": Optional[str],
                "tool_calls": List[Dict],
                "configs": List[str],  # List of <scraper_config> XML strings
                "done": bool,
                "raw_xml": str  # Cleaned XML for further processing
            }
        """
        result = {
            "valid": False,
            "error": None,
            "message": None,
            "tool_calls": [],
            "configs": [],
            "done": False,
            "raw_xml": ""
        }

        try:
            # Step 1: Clean and extract XML
            cleaned_xml = XMLConfigParser._clean_xml(ai_response)
            if not cleaned_xml:
                result["error"] = "No valid XML found in response"
                return result

            result["raw_xml"] = cleaned_xml

            # Step 2: Parse XML using ElementTree
            try:
                root = ET.fromstring(cleaned_xml)
            except ET.ParseError as e:
                result["error"] = f"XML parsing error: {str(e)}"
                return result

            # Step 3: Extract all components
            # Check if root is <xml> wrapper or direct <scraper_config>/<tool_call>
            if root.tag == "xml":
                # Parse wrapped XML
                result = XMLConfigParser._parse_wrapped_xml(root, result)
            elif root.tag == "scraper_config":
                # Direct scraper_config without wrapper
                config_str = ET.tostring(root, encoding='unicode', method='xml')
                result["configs"].append(config_str)
                result["valid"] = True
            elif root.tag == "tool_call":
                # Direct tool_call without wrapper
                tool_call = XMLConfigParser._parse_tool_call(root)
                if tool_call:
                    result["tool_calls"].append(tool_call)
                result["valid"] = True
            else:
                result["error"] = f"Unknown root tag: {root.tag}. Expected <xml>, <scraper_config>, or <tool_call>"
                return result

            # Step 4: Validate that response has meaningful content
            if not result["message"] and not result["tool_calls"] and not result["configs"] and not result["done"]:
                result["error"] = "XML is valid but contains no meaningful content (no message, tool_calls, configs, or status)"
                result["valid"] = False
                return result

            result["valid"] = True
            return result

        except Exception as e:
            result["error"] = f"Unexpected error during validation: {str(e)}"
            return result

    @staticmethod
    def _clean_xml(response: str) -> Optional[str]:
        """
        Clean XML from AI response (remove markdown, extra text, etc.).

        Args:
            response: Raw AI response

        Returns:
            Cleaned XML string or None if no XML found
        """
        response = response.strip()

        # Check for greetings or plain text before XML (REJECT these)
        greetings = ["hello", "hi", "i can", "i'll help", "here's", "here is", "let me help"]
        first_line = response.split('\n')[0].lower()[:100]
        if any(greeting in first_line for greeting in greetings):
            # Check if XML comes AFTER the greeting - this is invalid
            if '<xml>' in response or '<scraper_config>' in response or '<tool_call>' in response:
                # Has plain text before XML - INVALID
                return None

        # Case 1: Check if wrapped in markdown code block
        if "```xml" in response.lower() or "```" in response:
            # Extract content between code blocks
            match = re.search(r'```(?:xml)?\s*\n?(.*?)\n?```', response, re.DOTALL | re.IGNORECASE)
            if match:
                response = match.group(1).strip()

        # Case 2: Check if response starts with XML tag directly
        if not (response.startswith('<xml>') or
                response.startswith('<scraper_config>') or
                response.startswith('<tool_call>')):
            # Try to find XML tags
            xml_start_patterns = [
                r'<xml>',
                r'<scraper_config>',
                r'<tool_call>'
            ]

            found_xml = False
            for pattern in xml_start_patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    # Check if there's text before the XML tag
                    text_before = response[:match.start()].strip()
                    if text_before:
                        # Has text before XML - INVALID
                        return None
                    # Extract from the first XML tag to the end
                    response = response[match.start():]
                    found_xml = True
                    break

            if not found_xml:
                return None

        # Case 3: Remove any trailing text after closing tags
        xml_end_patterns = [
            (r'</xml>', 'xml'),
            (r'</scraper_config>', 'scraper_config'),
            (r'</tool_call>', 'tool_call')
        ]

        for pattern, tag in xml_end_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                # Extract up to and including the closing tag
                response = response[:match.end()]
                break

        # Final validation: Must start with an XML tag
        if not (response.startswith('<xml>') or
                response.startswith('<scraper_config>') or
                response.startswith('<tool_call>')):
            return None

        return response

    @staticmethod
    def _parse_wrapped_xml(root: ET.Element, result: Dict) -> Dict:
        """
        Parse <xml> wrapped response.
        
        Handles new structure:
        <xml>
          <message>...</message>
          <tool_calls>
            <tool_call>...</tool_call>
          </tool_calls>
          <scraper_config>...</scraper_config>
          <status>done</status>
        </xml>

        Args:
            root: XML root element (<xml>)
            result: Result dictionary to populate

        Returns:
            Updated result dictionary
        """
        # Extract <message>
        message_elem = root.find('message')
        if message_elem is not None and message_elem.text:
            result["message"] = message_elem.text.strip()

        # Extract <status> - supports "done", "DONE", "processing", etc.
        status_elem = root.find('status')
        if status_elem is not None and status_elem.text:
            status_text = status_elem.text.strip().upper()
            if status_text == "DONE":
                result["done"] = True
            # "processing" or other statuses mean not done yet
            result["status"] = status_text.lower()

        # Extract <tool_calls> wrapper (new format) or direct <tool_call> elements (backward compat)
        tool_calls_wrapper = root.find('tool_calls')
        if tool_calls_wrapper is not None:
            # New format: <tool_calls> contains multiple <tool_call>
            for tool_elem in tool_calls_wrapper.findall('tool_call'):
                tool_call = XMLConfigParser._parse_tool_call(tool_elem)
                if tool_call:
                    result["tool_calls"].append(tool_call)
        else:
            # Backward compat: direct <tool_call> elements at root level
            for tool_elem in root.findall('tool_call'):
                tool_call = XMLConfigParser._parse_tool_call(tool_elem)
                if tool_call:
                    result["tool_calls"].append(tool_call)

        # Extract all <scraper_config> elements
        for config_elem in root.findall('scraper_config'):
            config_str = ET.tostring(config_elem, encoding='unicode', method='xml')
            result["configs"].append(config_str)
            # If scraper_config exists, mark as done (config was provided)
            result["done"] = True

        return result

    @staticmethod
    def _parse_tool_call(tool_elem: ET.Element) -> Optional[Dict]:
        """
        Parse <tool_call> element.

        Args:
            tool_elem: <tool_call> XML element

        Returns:
            Dictionary with tool_name and args, or None if invalid
        """
        # Get tool name
        name_elem = tool_elem.find('name')
        if name_elem is None or not name_elem.text:
            return None

        tool_name = name_elem.text.strip()

        # Get args
        args_elem = tool_elem.find('args')
        if args_elem is None:
            return {"tool_name": tool_name, "args": {}}

        # Parse args (each child element is an argument)
        args = {}
        for arg_elem in args_elem:
            arg_name = arg_elem.tag
            arg_value = arg_elem.text.strip() if arg_elem.text else ""
            args[arg_name] = arg_value

        return {
            "tool_name": tool_name,
            "args": args
        }

    @staticmethod
    def create_error_feedback(validation_result: Dict[str, Any]) -> str:
        """
        Create error feedback message to send back to AI.

        Args:
            validation_result: Result from validate_and_parse

        Returns:
            Error feedback message in XML format
        """
        error_msg = validation_result.get("error", "Unknown validation error")

        feedback = f"""<xml>
<message>ERROR: {error_msg}

You MUST respond in valid XML format following this EXACT structure:

&lt;xml&gt;
  &lt;message&gt;Optional explanation&lt;/message&gt;
  &lt;tool_calls&gt;
    &lt;tool_call&gt;
      &lt;name&gt;tool_name&lt;/name&gt;
      &lt;args&gt;
        &lt;arg_name&gt;arg_value&lt;/arg_name&gt;
      &lt;/args&gt;
    &lt;/tool_call&gt;
  &lt;/tool_calls&gt;
  &lt;scraper_config&gt;
    <!-- Full config structure here -->
  &lt;/scraper_config&gt;
  &lt;status&gt;done&lt;/status&gt;
&lt;/xml&gt;

Rules:
1. ALWAYS start with &lt;xml&gt; and end with &lt;/xml&gt;
2. ALWAYS include &lt;status&gt;done&lt;/status&gt; or &lt;status&gt;processing&lt;/status&gt;
3. Tool calls go inside &lt;tool_calls&gt; wrapper
4. All content must be INSIDE the &lt;xml&gt; wrapper

Please retry with valid XML format.</message>
<status>processing</status>
</xml>"""

        return feedback

    # ============================================================================
    # CONFIG PARSING (XML to Dictionary)
    # ============================================================================

    @staticmethod
    def parse_configs_xml(xml_string: str) -> List[Dict]:
        """
        Parse XML that may contain multiple scraper_config blocks.

        Args:
            xml_string: XML string that may contain multiple <scraper_config> blocks

        Returns:
            List of config dictionaries
        """
        # Clean XML string
        xml_string = xml_string.strip()
        if xml_string.startswith("```xml"):
            xml_string = xml_string.replace("```xml", "").replace("```", "").strip()

        configs = []

        # Try to find multiple scraper_config blocks
        pattern = r'<scraper_config>(.*?)</scraper_config>'
        matches = re.finditer(pattern, xml_string, re.DOTALL)

        for match in matches:
            single_config_xml = f"<scraper_config>{match.group(1)}</scraper_config>"
            try:
                config = XMLConfigParser.parse_config_xml(single_config_xml)
                if config:
                    configs.append(config)
            except Exception:
                # Skip invalid config
                continue

        # If no matches found, try parsing as single config
        if not configs:
            try:
                single_config = XMLConfigParser.parse_config_xml(xml_string)
                if single_config:
                    configs.append(single_config)
            except Exception:
                pass

        return configs

    @staticmethod
    def parse_config_xml(xml_string: str, config_name: str = None) -> Dict:
        """
        Parse XML configuration into config dictionary (new multi-entity format).

        Expected XML structure:
        <scraper_config>
            <name>config_file_name</name>
            <metadata>...</metadata>
            <entities>
                <entity name="bitcoin">
                    <metric>
                        <name>energy_consumption</name>
                        <resources>...</resources>
                    </metric>
                </entity>
            </entities>
        </scraper_config>

        Args:
            xml_string: XML string from AI
            config_name: Override config name (optional)

        Returns:
            Config dictionary ready for saving
        """
        # Clean XML string
        xml_string = xml_string.strip()
        if xml_string.startswith("```xml"):
            xml_string = xml_string.replace("```xml", "").replace("```", "").strip()

        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML: {e}") from e

        # Parse config name
        name_elem = root.find("name")
        extracted_name = name_elem.text.strip() if name_elem is not None and name_elem.text else None
        name = config_name or extracted_name or "unnamed_config"

        # Parse metadata
        metadata_dict = XMLConfigParser._parse_metadata_dict(root.find("metadata"))

        # Parse entities
        entities_dict = {}
        entities_elem = root.find("entities")
        if entities_elem is not None:
            for entity_elem in entities_elem.findall("entity"):
                entity_name = entity_elem.get("name")
                if not entity_name:
                    continue

                metrics = []
                for metric_elem in entity_elem.findall("metric"):
                    metric = XMLConfigParser._parse_metric(metric_elem)
                    if metric:
                        metrics.append(metric)

                if metrics:
                    entities_dict[entity_name] = metrics

        return {
            "config_name": name,  # Include config name in result
            "metadata": metadata_dict,
            "entities": entities_dict
        }

    @staticmethod
    def _parse_metadata_dict(metadata_elem: Optional[ET.Element]) -> Dict:
        """Parse metadata element into dictionary."""
        if metadata_elem is None:
            return {
                "data_type": "single_value",
                "expected_format": "Unknown",
                "created_at": datetime.utcnow().isoformat(),
                "capture_date": datetime.utcnow().isoformat()
            }

        return {
            "data_type": XMLConfigParser._get_text(metadata_elem, "data_type", "single_value"),
            "expected_format": XMLConfigParser._get_text(metadata_elem, "expected_format", ""),
            "sample_value": XMLConfigParser._get_text(metadata_elem, "sample_value"),
            "update_frequency": XMLConfigParser._get_text(metadata_elem, "update_frequency", "daily"),
            "requires_auth": XMLConfigParser._get_text(metadata_elem, "requires_auth", "false").lower() == "true",
            "is_paginated": XMLConfigParser._get_text(metadata_elem, "is_paginated", "false").lower() == "true",
            "created_at": datetime.utcnow().isoformat(),
            "capture_date": XMLConfigParser._get_text(metadata_elem, "capture_date") or datetime.utcnow().isoformat(),
            "tags": []
        }

    @staticmethod
    def _parse_metric(metric_elem: ET.Element) -> Optional[Dict]:
        """Parse metric element into dictionary."""
        name_elem = metric_elem.find("name")
        if name_elem is None or not name_elem.text:
            return None

        metric_name = name_elem.text.strip()

        # Parse resources
        resources = []
        resources_elem = metric_elem.find("resources")
        if resources_elem is not None:
            for resource_elem in resources_elem.findall("resource"):
                resource = XMLConfigParser._parse_resource_dict(resource_elem)
                if resource:
                    resources.append(resource)

        if not resources:
            return None

        return {
            "name": metric_name,
            "resources": resources
        }

    @staticmethod
    def _parse_resource_dict(resource_elem: ET.Element) -> Optional[Dict]:
        """Parse single resource element into dictionary."""
        url_elem = resource_elem.find("url")
        if url_elem is None or not url_elem.text:
            return None

        url = url_elem.text.strip()

        # Parse headers
        headers = {}
        headers_elem = resource_elem.find("headers")
        if headers_elem is not None:
            for header_elem in headers_elem.findall("header"):
                name = header_elem.get("name")
                value = header_elem.get("value")
                if name and value:
                    headers[name] = value

        # Parse path (BeautifulSoup style)
        path = None
        path_elem = resource_elem.find("path")
        if path_elem is not None:
            path = []
            for step_elem in path_elem.findall("step"):
                step = {
                    "tag": step_elem.get("tag"),
                    "attribute": {
                        step_elem.get("attribute"): step_elem.get("value")
                    } if step_elem.get("attribute") else {}
                }
                path.append(step)

        # Parse action methods
        actions = []
        actions_elem = resource_elem.find("actions_methods")
        if actions_elem is not None:
            for action_elem in actions_elem.findall("action"):
                if action_elem.text:
                    actions.append(action_elem.text.strip())

        return {
            "url": url,
            "resource_type": XMLConfigParser._get_text(resource_elem, "resource_type", "html_static"),
            "api_path": XMLConfigParser._get_text(resource_elem, "api_path") or None,
            "method": XMLConfigParser._get_text(resource_elem, "method", "get"),
            "headers": headers,
            "xpath": XMLConfigParser._get_text(resource_elem, "xpath") or None,
            "path": path,
            "is_render_required": XMLConfigParser._get_text(resource_elem, "is_render_required", "false").lower() == "true",
            "is_captcha_based": XMLConfigParser._get_text(resource_elem, "is_captcha_based", "false").lower() == "true",
            "sleep_time": int(XMLConfigParser._get_text(resource_elem, "sleep_time", "5")),
            "locator_click": XMLConfigParser._get_text(resource_elem, "locator_click") or None,
            "pre_actions_methods": [],  # TODO: parse if present
            "actions_methods": actions,
            "extra_method": None,
            "extra_method_kwargs": {},
            "use_proxy": XMLConfigParser._get_text(resource_elem, "use_proxy", "false").lower() == "true",
            "timeout": int(XMLConfigParser._get_text(resource_elem, "timeout", "30")),
            "retries": int(XMLConfigParser._get_text(resource_elem, "retries", "3"))
        }

    @staticmethod
    def _get_text(element: ET.Element, tag: str, default: str = "") -> str:
        """Safely get text from XML element."""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return default

    # ============================================================================
    # XML BUILDING (Formatting data as XML)
    # ============================================================================

    @staticmethod
    def format_pre_analysis_xml(analysis: Dict[str, Any]) -> str:
        """
        Format pre-analysis results as XML for AI consumption.

        Converts pre-processing analysis results (from URL preprocessing)
        into structured XML format that can be included in user prompts.

        Args:
            analysis: Dictionary with pre-analysis results containing:
                - url: Target URL
                - content_type: Content type (json/html)
                - is_json: Boolean if content is JSON
                - is_render_required: Boolean if rendering needed
                - structure_info: Dict with structure details (for JSON)
                - apis: List of discovered APIs
                - js_files: List of JS files found

        Returns:
            XML string formatted as <pre_analysis>...</pre_analysis>
        """
        lines = ["<pre_analysis>"]

        lines.append(f"  <url>{analysis['url']}</url>")
        lines.append(f"  <content_type>{analysis.get('content_type', 'unknown')}</content_type>")
        lines.append(f"  <is_json>{str(analysis.get('is_json', False)).lower()}</is_json>")
        lines.append(f"  <is_render_required>{str(analysis.get('is_render_required', False)).lower()}</is_render_required>")

        # Structure info (for JSON responses)
        if analysis.get("structure_info"):
            struct = analysis["structure_info"]
            lines.append("  <structure_info>")

            if struct.get("type") == "list":
                lines.append("    <type>list</type>")
                lines.append(f"    <count>{struct.get('count', 0)}</count>")
                if struct.get("sample_item_keys"):
                    keys_str = ", ".join(struct["sample_item_keys"][:10])
                    lines.append(f"    <sample_keys>{keys_str}</sample_keys>")

            elif struct.get("type") == "object":
                lines.append("    <type>object</type>")
                keys_str = ", ".join(struct.get("keys", [])[:10])
                lines.append(f"    <keys>{keys_str}</keys>")

            lines.append("  </structure_info>")

        # APIs discovered
        if analysis.get("apis"):
            lines.append("  <discovered_apis>")
            for api in analysis["apis"][:10]:  # Limit to 10
                lines.append("    <api>")
                lines.append(f"      <url>{api.get('url', '')}</url>")
                lines.append(f"      <method>{api.get('method', 'GET')}</method>")
                lines.append(f"      <status>{api.get('status', 0)}</status>")

                if api.get("request_headers"):
                    lines.append(f"      <request_headers>{json.dumps(api['request_headers'])}</request_headers>")

                if api.get("response_headers"):
                    lines.append(f"      <response_headers>{json.dumps(api['response_headers'])}</response_headers>")

                if api.get("matched_keywords"):
                    lines.append(f"      <matched_keywords>{', '.join(api['matched_keywords'])}</matched_keywords>")

                lines.append("    </api>")
            lines.append("  </discovered_apis>")

        # JS files
        if analysis.get("js_files"):
            lines.append("  <js_files>")
            for js in analysis["js_files"][:5]:  # Limit to 5
                lines.append("    <js_file>")
                lines.append(f"      <url>{js.get('url', '')}</url>")
                lines.append(f"      <type>{js.get('type', 'unknown')}</type>")

                if js.get("has_interceptor"):
                    lines.append("      <has_interceptor>true</has_interceptor>")

                lines.append("    </js_file>")
            lines.append("  </js_files>")

        lines.append("</pre_analysis>")
        return "\n".join(lines)
