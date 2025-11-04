"""

Execution Engine - Execute complete scraping workflows

"""



import asyncio

import logging

from datetime import datetime

from typing import Dict, List, Any, Optional



from ..config.manager import ConfigManager

from .resource_processor import ResourceProcessor



logger = logging.getLogger(__name__)





class ExecutionEngine:

    """Execute scraping workflows"""



    def __init__(

        self,

        config_manager: ConfigManager,

        proxies: Optional[Dict] = None,

        browser=None,

        context=None

    ):

        """

        Initialize execution engine.



        Args:

            config_manager: ConfigManager instance

            proxies: Proxy configuration

            browser: Playwright browser

            context: Browser context

        """

        self.config_manager = config_manager

        self.processor = ResourceProcessor(proxies, browser, context)



    async def execute_single_config(

        self,

        config_name: str,

        custom_utils_module=None

    ) -> Dict[str, Any]:

        """

        Execute a single configuration file (all entities and metrics).



        Args:

            config_name: Name of config file to execute

            custom_utils_module: Optional custom utils module



        Returns:

            Dict with:

            {

                "config_name": "...",

                "success": bool,

                "data": List[{name, metric, value, date, config_name}],

                "errors": List[error_info]

            }

        """

        # Load config

        config = self.config_manager.load_config_object(config_name)

        if not config:

            return {

                "config_name": config_name,

                "success": False,

                "data": [],

                "error": "Config not found"

            }



        # Load utils module (config-specific or custom)

        if custom_utils_module:

            utils_module = custom_utils_module

        else:

            utils_module = self.config_manager.load_utils_module(config_name)



        # Collect all results

        results = []

        errors = []

        capture_date = datetime.utcnow().isoformat()



        # Iterate through all entities and their metrics

        for entity_name, metrics in config.entities.items():

            for metric_config in metrics:

                # Try all resources for this metric until one succeeds

                metric_value = None

                metric_errors = []



                for resource_idx, resource in enumerate(metric_config.resources):

                    try:

                        value = await self.processor.process_resource(resource, utils_module)



                        if value is not None:

                            metric_value = value

                            break  # Success, no need to try other resources



                    except Exception as e:

                        metric_errors.append({

                            "entity": entity_name,

                            "metric": metric_config.name,

                            "resource_idx": resource_idx,

                            "resource_url": resource.url,

                            "error": str(e)

                        })

                        logger.error(f"Resource failed for {entity_name}.{metric_config.name}: {e}")

                        continue



                # If we got a value, add to results

                if metric_value is not None:

                    results.append({

                        "name": entity_name,

                        "metric": metric_config.name,

                        "value": metric_value,

                        "date": capture_date,

                        "config_name": config_name

                    })

                else:

                    # All resources failed for this metric

                    errors.extend(metric_errors)



        return {

            "config_name": config_name,

            "success": len(results) > 0,

            "data": results,  # List of {name, metric, value, date, config_name}

            "errors": errors,

            "total_metrics": sum(len(metrics) for metrics in config.entities.values()),

            "successful_metrics": len(results),

            "failed_metrics": sum(len(metrics) for metrics in config.entities.values()) - len(results)

        }



    async def execute_multiple_configs(

        self,

        config_names: List[str],

        custom_utils_module=None,

        parallel: bool = True

    ) -> Dict[str, Dict]:

        """

        Execute multiple configurations.



        Args:

            config_names: List of config names

            custom_utils_module: Optional custom utils module

            parallel: Execute in parallel or sequential



        Returns:

            Dict mapping config names to results

        """

        if parallel:

            tasks = [

                self.execute_single_config(name, custom_utils_module)

                for name in config_names

            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)



            return {

                config_names[i]: results[i] if not isinstance(results[i], Exception) else {

                    "config_name": config_names[i],

                    "success": False,

                    "error": str(results[i])

                }

                for i in range(len(config_names))

            }

        else:

            results = {}

            for name in config_names:

                result = await self.execute_single_config(name, custom_utils_module)

                results[name] = result

            return results



    async def execute_all_configs(

        self,

        custom_utils_module=None,

        parallel: bool = True

    ) -> Dict[str, Dict]:

        """

        Execute all available configurations.



        Args:

            custom_utils_module: Optional custom utils module

            parallel: Execute in parallel or sequential



        Returns:

            Dict mapping config names to results

        """

        config_names = self.config_manager.list_config_names()



        if not config_names:

            logger.warning("No configurations found")

            return {}



        return await self.execute_multiple_configs(

            config_names,

            custom_utils_module,

            parallel

        )
