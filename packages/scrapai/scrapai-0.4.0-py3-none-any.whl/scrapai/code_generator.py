"""

Code Generator for ScrapAI SDK

Generates executable Python code from configurations

"""



import json

from typing import Dict, Optional

from .config.manager import ConfigManager





class CodeGenerator:

    """Generates Python code from scraping configurations"""



    def __init__(self, config_manager: ConfigManager):

        """

        Initialize CodeGenerator.



        Args:

            config_manager: ConfigManager instance

        """

        self.config_manager = config_manager



    def generate_code(self, config_name: str, include_utils: bool = True) -> str:

        """

        Generate Python code string for executing a config.



        Args:

            config_name: Name of config to generate code for

            include_utils: Whether to include utils loading code



        Returns:

            Python code as string

        """

        config = self.config_manager.load_config(config_name)



        if not config:

            return f"# Config '{config_name}' not found"



        code_lines = [

            "#!/usr/bin/env python3",

            '"""',

            f"Generated code for config: {config_name}",

            '"""',

            "",

            "# Imports",

            "import asyncio",

            "import json",

            "from pathlib import Path",

            "",

            "# Import base utilities",

            "from scrapai.base_utils import (",

            "    call_api,",

            "    render_website,",

            "    parse_html_with_xpath,",

            "    parse_html_with_path,",

            "    deep_access,",

            "    apply_action_methods",

            ")",

            "",

            "# Config data",

            f"CONFIG = {self._format_config(config)}",

            ""

        ]



        # Add utils loading if config-specific utils exist

        if include_utils and self.config_manager.utils_exists(config_name):

            code_lines.extend([

                "# Load config-specific utils (optional)",

                f"import sys",

                f"utils_path = Path('.scrapai/utils/{config_name}_utils.py')",

                f"if utils_path.exists():",

                f"    import importlib.util",

                f"    spec = importlib.util.spec_from_file_location('utils', utils_path)",

                f"    utils = importlib.util.module_from_spec(spec)",

                f"    spec.loader.exec_module(utils)",

                f"else:",

                f"    utils = None",

                "",

            ])

        else:

            code_lines.append("utils = None  # No config-specific utils")

            code_lines.append("")



        # Add execution code

        code_lines.extend([

            "async def execute():",

            "    \"\"\"Execute the scraping configuration\"\"\"",

            "    config = CONFIG",

            "    resources = config.get('resources', [])",

            "    metric_name = config.get('name', 'value')",

            "",

            "    # Process each resource until one succeeds",

            "    for resource in resources:",

            "        try:",

            "            value = await process_resource(resource)",

            "            if value is not None:",

            "                return {metric_name: value}",

            "        except Exception as e:",

            "            print(f'Resource failed: {e}')",

            "            continue",

            "",

            "    return {}",

            "",

            "",

            "async def process_resource(resource):",

            "    \"\"\"Process a single resource\"\"\"",

            "    url = resource.get('url')",

            "    ",

            "    # API resource",

            "    if resource.get('api_path'):",

            "        response = call_api(",

            "            url,",

            "            method=resource.get('method', 'get'),",

            "            headers=resource.get('headers', {}),",

            "            data=resource.get('data'),",

            "            use_proxy=resource.get('use_proxy', False)",

            "        )",

            "        value = deep_access(response, resource['api_path'])",

            "        ",

            "        # Apply actions",

            "        for action in resource.get('actions_methods', []):",

            "            if utils and hasattr(utils, action):",

            "                value = getattr(utils, action)(value)",

            "            else:",

            "                value = apply_action_methods(value, [action])",

            "        ",

            "        return value",

            "    ",

            "    # HTML resource (simplified - would need browser for rendering)",

            "    else:",

            "        import requests",

            "        response = requests.get(url, timeout=30)",

            "        html = response.text",

            "        ",

            "        if resource.get('xpath'):",

            "            value = parse_html_with_xpath(html, resource['xpath'])",

            "        elif resource.get('path'):",

            "            value = parse_html_with_path(html, resource['path'])",

            "        ",

            "        # Apply actions",

            "        for action in resource.get('actions_methods', []):",

            "            if utils and hasattr(utils, action):",

            "                value = getattr(utils, action)(value)",

            "            else:",

            "                value = apply_action_methods(value, [action])",

            "        ",

            "        return value",

            "",

            "",

            "if __name__ == '__main__':",

            "    result = asyncio.run(execute())",

            "    print(json.dumps(result, indent=2))",

            ""

        ])



        return "\n".join(code_lines)



    def _format_config(self, config: Dict) -> str:

        """Format config dict as Python code."""

        formatted = json.dumps(config, indent=4)

        # Replace with Python formatting

        return formatted.replace('null', 'None').replace('true', 'True').replace('false', 'False')
