"""

Config Runner - Test and execute configurations

"""



from typing import Dict, Any, Optional

from datetime import datetime



from ..config.schema import ScraperConfig, ResourceConfig

from ..crawler.resource_processor import ResourceProcessor





class ConfigRunner:

    """Run and test scraper configurations"""



    def __init__(self, proxies: Optional[Dict] = None, browser=None, context=None):

        """

        Initialize config runner.



        Args:

            proxies: Proxy configuration

            browser: Playwright browser instance

            context: Browser context

        """

        self.processor = ResourceProcessor(proxies, browser, context)



    async def run_config(self, config: ScraperConfig) -> Dict[str, Any]:

        """

        Run a complete configuration.



        Args:

            config: ScraperConfig to execute



        Returns:

            Execution result with extracted data and metadata

        """

        start_time = datetime.utcnow()

        result = {

            "config_name": config.name,

            "success": False,

            "data": None,

            "errors": [],

            "resources_tried": 0,

            "resources_succeeded": 0,

            "execution_time_seconds": 0

        }



        # Try each resource until one succeeds

        for idx, resource in enumerate(config.resources):

            result["resources_tried"] += 1



            try:

                data = await self.processor.process_resource(resource)



                if data is not None:

                    result["success"] = True

                    result["data"] = data

                    result["resources_succeeded"] = 1

                    break



            except Exception as e:

                error_info = {

                    "resource_index": idx,

                    "resource_url": resource.url,

                    "error": str(e)

                }

                result["errors"].append(error_info)



        end_time = datetime.utcnow()

        result["execution_time_seconds"] = (end_time - start_time).total_seconds()



        return result



    async def test_resource(self, resource: ResourceConfig) -> Dict[str, Any]:

        """

        Test a single resource.



        Args:

            resource: ResourceConfig to test



        Returns:

            Test result

        """

        start_time = datetime.utcnow()

        test_result = {

            "url": resource.url,

            "resource_type": resource.resource_type.value,

            "success": False,

            "data": None,

            "error": None,

            "execution_time_seconds": 0

        }



        try:

            data = await self.processor.process_resource(resource)

            test_result["success"] = data is not None

            test_result["data"] = data

        except Exception as e:

            test_result["error"] = str(e)



        end_time = datetime.utcnow()

        test_result["execution_time_seconds"] = (end_time - start_time).total_seconds()



        return test_result



    async def dry_run_config(self, config: ScraperConfig) -> Dict[str, Any]:

        """

        Dry run - validate config without actually executing.



        Args:

            config: Config to validate



        Returns:

            Validation result

        """

        validation = {

            "config_name": config.name,

            "is_valid": True,

            "warnings": [],

            "recommendations": []

        }



        # Check resources

        if not config.resources:

            validation["is_valid"] = False

            validation["warnings"].append("No resources defined")



        # Check each resource

        for idx, resource in enumerate(config.resources):

            # Check URL

            if not resource.url or not resource.url.startswith("http"):

                validation["is_valid"] = False

                validation["warnings"].append(f"Resource {idx}: Invalid URL")



            # Check API resources have api_path

            if resource.resource_type.value.startswith("api"):

                if not resource.api_path:

                    validation["warnings"].append(

                        f"Resource {idx}: API resource without api_path"

                    )



            # Check HTML resources have extraction method

            if resource.resource_type.value.startswith("html"):

                if not resource.xpath and not resource.path:

                    validation["warnings"].append(

                        f"Resource {idx}: HTML resource without xpath or path"

                    )



            # Check render requirements

            if resource.is_render_required and resource.sleep_time < 3:

                validation["recommendations"].append(

                    f"Resource {idx}: Rendered pages usually need sleep_time >= 3"

                )



            # Check CAPTCHA resources

            if resource.is_captcha_based:

                if not resource.use_proxy:

                    validation["recommendations"].append(

                        f"Resource {idx}: CAPTCHA pages work better with proxies"

                    )

                if resource.sleep_time < 15:

                    validation["recommendations"].append(

                        f"Resource {idx}: CAPTCHA solving needs sleep_time >= 15"

                    )



        return validation



    def compare_results(self, result1: Dict, result2: Dict) -> Dict[str, Any]:

        """

        Compare two execution results.



        Args:

            result1: First result

            result2: Second result



        Returns:

            Comparison analysis

        """

        comparison = {

            "both_succeeded": result1["success"] and result2["success"],

            "data_matches": False,

            "differences": []

        }



        if comparison["both_succeeded"]:

            data1 = result1["data"]

            data2 = result2["data"]



            if data1 == data2:

                comparison["data_matches"] = True

            else:

                comparison["differences"].append({

                    "type": "value_mismatch",

                    "value1": data1,

                    "value2": data2

                })

        else:

            if result1["success"] != result2["success"]:

                comparison["differences"].append({

                    "type": "success_status_mismatch",

                    "result1_success": result1["success"],

                    "result2_success": result2["success"]

                })



        return comparison
