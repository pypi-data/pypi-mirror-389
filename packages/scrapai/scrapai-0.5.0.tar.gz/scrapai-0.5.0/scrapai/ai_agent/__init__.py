"""
AI Agent module - Simple conversation history manager

The Agent class is a lightweight wrapper that manages conversation history
and provides interface to call AI models. All business logic is handled
by services in ai_services and ai_analyzer modules.
"""

from .agent import Agent

__all__ = ["Agent"]
