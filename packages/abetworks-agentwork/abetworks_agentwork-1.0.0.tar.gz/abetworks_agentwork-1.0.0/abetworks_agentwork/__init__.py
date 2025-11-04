
"""
Abetworks AgentWork SDK
Build AI agents for the Abetworks platform
"""

__version__ = "1.0.0"

from .base import BaseAgent, AgentResponse, AgentError
from .flask_agent import FlaskAgent
from .fastapi_agent import FastAPIAgent
from .client import AbetworksClient

__all__ = [
    "BaseAgent",
    "AgentResponse",
    "AgentError",
    "FlaskAgent",
    "FastAPIAgent",
    "AbetworksClient",
]
