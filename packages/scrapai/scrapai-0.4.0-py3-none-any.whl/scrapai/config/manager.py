"""

Config Manager - Manage scraping configurations with metadata

"""



import json

import importlib.util

import sys

import logging

from pathlib import Path

from typing import List, Optional

from datetime import datetime



from .schema import ScraperConfig



logger = logging.getLogger(__name__)





class ConfigManager:

    """Manage scraping configurations"""



    def __init__(self, base_path: str = "."):

        """

        Initialize config manager.



        Args:

            base_path: Base directory containing .scrapai folder

        """

        self.base_path = Path(base_path)

        self.scrapai_dir = self.base_path / ".scrapai"

        self.configs_dir = self.scrapai_dir / "configs"

        self.utils_dir = self.scrapai_dir / "utils"



        # Ensure directories exist

        self.configs_dir.mkdir(parents=True, exist_ok=True)

        self.utils_dir.mkdir(parents=True, exist_ok=True)



    def list_config_names(self) -> List[str]:

        """

        List all available configuration names.



        Returns:

            List of config names (without .json extension)

        """

        if not self.configs_dir.exists():

            return []



        return [

            f.stem for f in self.configs_dir.glob("*.json")

        ]



    def config_exists(self, config_name: str) -> bool:

        """Check if config exists."""

        config_path = self.configs_dir / f"{config_name}.json"

        return config_path.exists()



    def utils_exists(self, config_name: str) -> bool:

        """Check if config-specific utils exist."""

        utils_path = self.utils_dir / f"{config_name}_utils.py"

        return utils_path.exists()



    def load_config_dict(self, config_name: str) -> Optional[dict]:

        """

        Load configuration as dictionary.



        Args:

            config_name: Name of config



        Returns:

            Config dict or None

        """

        config_path = self.configs_dir / f"{config_name}.json"



        if not config_path.exists():

            logger.warning(f"Config not found: {config_name}")

            return None



        try:

            with open(config_path, 'r') as f:

                return json.load(f)

        except Exception as e:

            logger.error(f"Failed to load config {config_name}: {e}")

            return None



    def load_config_object(self, config_name: str) -> Optional[ScraperConfig]:

        """

        Load configuration as ScraperConfig object.



        Args:

            config_name: Name of config



        Returns:

            ScraperConfig object or None

        """

        config_dict = self.load_config_dict(config_name)



        if not config_dict:

            return None



        try:

            return ScraperConfig.from_dict(config_name, config_dict)

        except Exception as e:

            logger.error(f"Failed to parse config {config_name}: {e}")

            return None



    def save_config(self, config_name: str, config: ScraperConfig) -> bool:

        """

        Save configuration.



        Args:

            config_name: Name of config

            config: ScraperConfig object



        Returns:

            True if successful

        """

        config_path = self.configs_dir / f"{config_name}.json"



        try:

            # Update timestamps

            config.metadata.updated_at = datetime.utcnow().isoformat()

            if not config.metadata.created_at:

                config.metadata.created_at = datetime.utcnow().isoformat()



            # Save to file

            with open(config_path, 'w') as f:

                json.dump(config.to_dict(), f, indent=2)



            logger.info(f"Config saved: {config_name}")

            return True



        except Exception as e:

            logger.error(f"Failed to save config {config_name}: {e}")

            return False



    def save_config_dict(self, config_name: str, config_dict: dict) -> bool:

        """

        Save configuration from dictionary (used by agent).



        Args:

            config_name: Name of config

            config_dict: Config dictionary



        Returns:

            True if successful

        """

        config_path = self.configs_dir / f"{config_name}.json"



        try:

            # Ensure metadata has timestamps

            if "metadata" not in config_dict:

                config_dict["metadata"] = {}



            config_dict["metadata"]["updated_at"] = datetime.utcnow().isoformat()

            if "created_at" not in config_dict["metadata"]:

                config_dict["metadata"]["created_at"] = datetime.utcnow().isoformat()



            # Save to file

            with open(config_path, 'w') as f:

                json.dump(config_dict, f, indent=2)



            logger.info(f"Config saved: {config_name}")

            return True



        except Exception as e:

            logger.error(f"Failed to save config {config_name}: {e}")

            return False



    def remove_config(self, config_name: str) -> bool:

        """

        Remove configuration and its utils.



        Args:

            config_name: Name of config to remove



        Returns:

            True if successful

        """

        config_path = self.configs_dir / f"{config_name}.json"

        utils_path = self.utils_dir / f"{config_name}_utils.py"



        success = True



        # Remove config file

        if config_path.exists():

            try:

                config_path.unlink()

                logger.info(f"Removed config: {config_name}")

            except Exception as e:

                logger.error(f"Failed to remove config {config_name}: {e}")

                success = False



        # Remove utils file

        if utils_path.exists():

            try:

                utils_path.unlink()

                logger.info(f"Removed utils for {config_name}")

            except Exception as e:

                logger.error(f"Failed to remove utils for {config_name}: {e}")



        return success



    def save_utils_code(self, config_name: str, utils_code: str) -> bool:

        """

        Save config-specific utils code.



        Args:

            config_name: Name of config

            utils_code: Python code for utils



        Returns:

            True if successful

        """

        utils_path = self.utils_dir / f"{config_name}_utils.py"



        try:

            with open(utils_path, 'w') as f:

                f.write(utils_code)

            logger.info(f"Utils saved for {config_name}")

            return True

        except Exception as e:

            logger.error(f"Failed to save utils for {config_name}: {e}")

            return False



    def load_utils_module(self, config_name: str):

        """

        Load config-specific utils module.



        Args:

            config_name: Name of config



        Returns:

            Loaded module or None

        """

        utils_path = self.utils_dir / f"{config_name}_utils.py"



        if not utils_path.exists():

            return None



        try:

            spec = importlib.util.spec_from_file_location(

                f"{config_name}_utils",

                str(utils_path)

            )



            if spec and spec.loader:

                module = importlib.util.module_from_spec(spec)

                sys.modules[f"{config_name}_utils"] = module

                spec.loader.exec_module(module)

                logger.info(f"Loaded utils module for {config_name}")

                return module

        except Exception as e:

            logger.error(f"Failed to load utils for {config_name}: {e}")



        return None



    def get_config_metadata(self, config_name: str) -> Optional[dict]:

        """

        Get only metadata from config.



        Args:

            config_name: Name of config



        Returns:

            Metadata dict or None

        """

        config_dict = self.load_config_dict(config_name)



        if config_dict:

            return config_dict.get("metadata", {})



        return None
