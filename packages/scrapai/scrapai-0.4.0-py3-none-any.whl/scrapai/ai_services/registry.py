"""

AI Service Registry - Known AI service endpoints

"""



from typing import Dict, Optional

import logging



logger = logging.getLogger(__name__)





class AIServiceRegistry:

    """Registry of known AI services and their endpoints"""



    # Known services with their default base URLs

    KNOWN_SERVICES: Dict[str, Dict[str, str]] = {

        "openai": {

            "base_url": "https://api.openai.com/v1",

            "default_model": "gpt-4",

            "api_key_header": "Authorization"

        },

        "ollama": {

            "base_url": "http://localhost:11434/v1",  # Default local Ollama

            "default_model": "gpt-oss:120b-cloud",

            "api_key_header": "Authorization"  # Often not required for local

        },

        "grok": {

            "base_url": "https://api.x.ai/v1",

            "default_model": "grok-beta",

            "api_key_header": "Authorization"

        },

        "anthropic": {

            "base_url": "https://api.anthropic.com/v1",

            "default_model": "claude-3-opus-20240229",

            "api_key_header": "x-api-key"

        },

        "google": {

            "base_url": "https://generativelanguage.googleapis.com/v1",

            "default_model": "gemini-pro",

            "api_key_header": "x-goog-api-key"

        },

        "mistral": {

            "base_url": "https://api.mistral.ai/v1",

            "default_model": "mistral-medium",

            "api_key_header": "Authorization"

        },

        "cohere": {

            "base_url": "https://api.cohere.ai/v1",

            "default_model": "command",

            "api_key_header": "Authorization"

        },

        "together": {

            "base_url": "https://api.together.xyz/v1",

            "default_model": "meta-llama/Llama-2-70b-chat-hf",

            "api_key_header": "Authorization"

        },

        "openrouter": {

            "base_url": "https://openrouter.ai/api/v1",

            "default_model": "openai/gpt-4",

            "api_key_header": "Authorization"

        },

        "perplexity": {

            "base_url": "https://api.perplexity.ai",

            "default_model": "pplx-70b-online",

            "api_key_header": "Authorization"

        },

        "deepseek": {

            "base_url": "https://api.deepseek.com/v1",

            "default_model": "deepseek-chat",

            "api_key_header": "Authorization"

        },

        "localai": {

            "base_url": "http://localhost:8080/v1",  # Common LocalAI endpoint

            "default_model": "gpt-3.5-turbo",

            "api_key_header": "Authorization"

        }

    }



    @classmethod

    def get_service_info(cls, service_name: str) -> Optional[Dict[str, str]]:

        """

        Get service information by name.



        Args:

            service_name: Service name (case-insensitive)



        Returns:

            Service info dict or None

        """

        service_lower = service_name.lower().strip()

        return cls.KNOWN_SERVICES.get(service_lower)



    @classmethod

    def list_services(cls) -> list:

        """List all known service names."""

        return list(cls.KNOWN_SERVICES.keys())



    @classmethod

    def search_service_endpoint(cls, service_name: str) -> Optional[str]:

        """

        Search for service endpoint (from known services).

        In future, could add web search here.



        Args:

            service_name: Service name to search



        Returns:

            Base URL if found, None otherwise

        """

        service_info = cls.get_service_info(service_name)

        if service_info:

            return service_info.get("base_url")



        # Could add web search here for unknown services

        # For now, return None

        logger.warning(f"Service '{service_name}' not in registry. "

                      f"Available services: {cls.list_services()}")

        return None



    @classmethod

    def get_default_model(cls, service_name: str) -> str:

        """Get default model for service."""

        service_info = cls.get_service_info(service_name)

        if service_info:

            return service_info.get("default_model", "gpt-4")

        return "gpt-4"  # Fallback



    @classmethod

    def is_service_known(cls, service_name: str) -> bool:

        """Check if service is in registry."""

        return service_name.lower().strip() in cls.KNOWN_SERVICES
