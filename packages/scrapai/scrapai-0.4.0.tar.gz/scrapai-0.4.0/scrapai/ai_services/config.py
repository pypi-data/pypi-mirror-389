"""

AI Service Configuration - Auto-configure AI clients

"""



from typing import Optional, Dict

import logging

from openai import OpenAI



from .registry import AIServiceRegistry



logger = logging.getLogger(__name__)





class AIServiceConfig:

    """AI Service Configuration and Client Builder"""



    def __init__(

        self,

        service_name: str,

        api_key: str,

        base_url: Optional[str] = None,

        model: Optional[str] = None

    ):

        """

        Initialize AI service configuration.



        Args:

            service_name: Name of AI service (openai, ollama, grok, etc.)

            api_key: API key for the service

            base_url: Optional custom base URL (auto-detected if None)

            model: Optional model name (uses service default if None)

        """

        self.service_name = service_name.lower().strip()

        self.api_key = api_key

        self.base_url = base_url

        self.model = model

        self._enable_logging = False  # Set by caller



        # Auto-configure if needed

        self._auto_configure()



    def _auto_configure(self):

        """Auto-configure base_url and model if not provided."""

        service_info = AIServiceRegistry.get_service_info(self.service_name)



        if service_info:

            # Auto-set base_url if not provided

            if not self.base_url:

                self.base_url = service_info.get("base_url")

                if self._enable_logging:

                    logger.info(f"Auto-detected base_url for {self.service_name}: {self.base_url}")



            # Auto-set model if not provided

            if not self.model:

                self.model = service_info.get("default_model")

                if self._enable_logging:

                    logger.info(f"Auto-detected model for {self.service_name}: {self.model}")

        else:

            # Unknown service - user must provide base_url

            if not self.base_url:

                logger.warning(

                    f"Unknown service '{self.service_name}'. "

                    f"Please provide base_url. Known services: {AIServiceRegistry.list_services()}"

                )

            else:

                if self._enable_logging:

                    logger.info(f"Using custom base_url for unknown service: {self.base_url}")



            # Use default model if not provided

            if not self.model:

                self.model = "gpt-4"  # Fallback



    @property

    def enable_logging(self) -> bool:

        """Check if logging is enabled (for compatibility)."""

        return self._enable_logging



    @enable_logging.setter

    def enable_logging(self, value: bool):

        self._enable_logging = value



    def create_client(self) -> OpenAI:

        """

        Create OpenAI-compatible client for the service.



        Returns:

            OpenAI client instance configured for the service

        """

        client_kwargs = {

            "api_key": self.api_key

        }



        # Add base_url if provided (required for non-OpenAI services)

        if self.base_url:

            client_kwargs["base_url"] = self.base_url



        try:

            client = OpenAI(**client_kwargs)

            return client

        except Exception as e:

            logger.error(f"Failed to create client for {self.service_name}: {e}")

            raise



    def get_model(self) -> str:

        """Get model name."""

        return self.model or "gpt-4"



    def to_dict(self) -> Dict:

        """Convert to dictionary."""

        return {

            "service_name": self.service_name,

            "base_url": self.base_url,

            "model": self.model,

            "has_api_key": bool(self.api_key)

        }
