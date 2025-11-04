"""
Agent - Conversation history manager and AI model caller

Simple wrapper that manages conversation history and provides interface
to call AI models. All business logic is handled by services.
"""


import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from collections import deque
from pathlib import Path

from ..ai_services.config import AIServiceConfig


class Agent:
    """
    Conversation history manager and AI model interface.
    
    This is a simple wrapper that:
    - Manages conversation history (last N messages)
    - Provides interface to call AI models
    - Handles conversation logging
    
    All business logic (preprocessing, analysis, config creation) is handled
    by services that use this agent.
    """

    def __init__(
        self,
        service_config: AIServiceConfig,
        max_context_messages: int = 25,
        enable_logging: bool = True
    ):
        """
        Initialize agent.

        Args:
            service_config: AIServiceConfig with service configuration
            max_context_messages: Maximum number of messages to keep in history
            enable_logging: Enable/disable logging output
        """
        self.enable_logging = enable_logging
        self.service_config = service_config
        
        # Create AI client
        self.client = service_config.create_client()
        self.model = service_config.get_model()

        # Conversation history (last N messages - only user/assistant, not system)
        self.max_context_messages = max_context_messages
        self.conversation_history = deque(maxlen=max_context_messages)
        
        # System prompt (stored separately, not in history)
        self.system_prompt: Optional[Dict[str, str]] = None

    def _log(self, level: str, message: str):
        """
        Centralized logging method.

        Args:
            level: Log level (INFO, DEBUG, WARNING, ERROR)
            message: Log message
        """
        if self.enable_logging:
            prefix = f"[{level}]" if level else ""
            print(f"{prefix} {message}")

    def call_model(self, messages: Union[List[Dict[str, str]], Dict[str, str]]) -> str:
        """
        Call the AI model using agent's maintained history + new messages.
        
        Agent maintains conversation history internally. 
        
        First call: Pass list of messages (including system prompt + initial user message)
        Subsequent calls: Pass single dict (just the new user message)
        
        This method:
        1. If list: extracts system prompt (stores it) and user messages (adds to history)
        2. If dict: adds single user message to history
        3. Builds complete messages: system prompt + conversation history
        4. Calls the model with combined messages
        5. Adds assistant response to history
        6. Returns the content string

        Args:
            messages: First call: List with system + user messages. 
                     Subsequent calls: Single dict with user message

        Returns:
            AI response content as string
        """
        try:
            # Handle both list (first call) and dict (subsequent calls)
            if isinstance(messages, dict):
                # Subsequent call: just add single user message to history
                self.add_to_history("user", messages.get("content", ""))
            elif isinstance(messages, list):
                # First call: extract system prompt and user messages
                system_msg = None
                for msg in messages:
                    role = msg.get("role", "")
                    if role == "system":
                        # Store system prompt separately
                        system_msg = msg
                        self.system_prompt = msg
                    elif role == "user":
                        # Add user messages to history
                        self.add_to_history("user", msg.get("content", ""))
            
            # Build complete messages: system + history
            complete_messages = []
            
            # Add system prompt (must be stored from first call)
            if self.system_prompt:
                complete_messages.append(self.system_prompt)
            else:
                raise ValueError("System prompt not found. First call must include system prompt in messages list.")
            
            # Add conversation history (includes all previous exchanges)
            complete_messages.extend(self.get_conversation_history())
            
            # Call the model with combined messages
            response = self.client.chat.completions.create(
                model=self.model,
                messages=complete_messages,
                temperature=0.7
            )
            
            # Get response content
            content = response.choices[0].message.content
            
            # Add assistant response to history
            self.add_to_history("assistant", content)
            
            return content
        except Exception as e:
            self._log("ERROR", f"Model call failed: {e}")
            raise

    def add_to_history(self, role: str, content: str):
        """
        Add message to conversation history.

        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
        """
        self.conversation_history.append({
            "role": role,
            "content": content
        })

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get current conversation history.

        Returns:
            List of conversation messages
        """
        return list(self.conversation_history)

    def clear_conversation_history(self):
        """Clear all conversation history."""
        self.conversation_history.clear()

    def write_conversation_log(self, log_file: Path, messages: List[Dict[str, Any]]):
        """
        Write conversation messages to JSON file.

        Args:
            log_file: Path to log file
            messages: List of conversation messages with timestamps
        """
        try:
            log_data = {
                "conversation": messages,
                "timestamp": datetime.now().isoformat()
            }
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            self._log("ERROR", f"Could not write conversation log: {e}")
