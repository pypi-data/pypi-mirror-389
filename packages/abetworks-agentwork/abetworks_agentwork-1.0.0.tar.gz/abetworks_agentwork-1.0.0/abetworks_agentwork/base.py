
"""Base agent class and core models"""

from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod


class AgentResponse(BaseModel):
    """Standard response format for agent tasks"""
    status: str = Field(..., description="Status: success, error, or pending")
    output: Optional[Dict[str, Any]] = Field(None, description="Task output data")
    error: Optional[str] = Field(None, description="Error message if status is error")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AgentError(Exception):
    """Custom exception for agent errors"""
    pass


class BaseAgent(ABC):
    """Base class for all Abetworks agents"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        api_key: str,
        description: str = "",
        version: str = "1.0.0"
    ):
        self.agent_id = agent_id
        self.name = name
        self.api_key = api_key
        self.description = description
        self.version = version
        self.tasks: Dict[str, Callable] = {}
    
    def task(self, task_name: str):
        """Decorator to register a task handler"""
        def decorator(func: Callable):
            self.tasks[task_name] = func
            return func
        return decorator
    
    def validate_org_id(self, org_id: str) -> bool:
        """Validate organization ID"""
        if not org_id or not isinstance(org_id, str):
            raise AgentError("Invalid org_id")
        return True
    
    def validate_api_key(self, provided_key: str) -> bool:
        """Validate API key"""
        return provided_key == self.api_key
    
    @abstractmethod
    def register_routes(self, app):
        """Register routes with the web framework"""
        pass
    
    def execute_task(
        self,
        task_name: str,
        input_data: Dict[str, Any],
        org_id: str,
        task_id: Optional[str] = None
    ) -> AgentResponse:
        """Execute a registered task"""
        self.validate_org_id(org_id)
        
        if task_name not in self.tasks:
            return AgentResponse(
                status="error",
                error=f"Unknown task: {task_name}"
            )
        
        try:
            result = self.tasks[task_name](input_data, org_id, task_id)
            if isinstance(result, AgentResponse):
                return result
            elif isinstance(result, dict):
                return AgentResponse(status="success", output=result)
            else:
                return AgentResponse(
                    status="success",
                    output={"result": result}
                )
        except Exception as e:
            return AgentResponse(
                status="error",
                error=str(e)
            )
