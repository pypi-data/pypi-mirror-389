
"""FastAPI agent implementation"""

from fastapi import Header, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from .base import BaseAgent, AgentResponse, AgentError


class ExecuteRequest(BaseModel):
    """Request model for task execution"""
    org_id: str
    task_name: str = "default"
    input_data: Dict[str, Any] = {}
    task_id: Optional[str] = None


class FastAPIAgent(BaseAgent):
    """Agent implementation for FastAPI applications"""
    
    def register_routes(self, app):
        """Register FastAPI routes for the agent"""
        
        @app.get("/health")
        async def health():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "version": self.version
            }
        
        @app.post("/execute", response_model=AgentResponse)
        async def execute(
            request: ExecuteRequest,
            x_api_key: str = Header(None, alias="X-API-Key")
        ):
            """Main execution endpoint"""
            # Validate API key
            if not self.validate_api_key(x_api_key):
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            # Validate org_id
            try:
                self.validate_org_id(request.org_id)
            except AgentError as e:
                raise HTTPException(status_code=400, detail=str(e))
            
            # Execute task
            response = self.execute_task(
                request.task_name,
                request.input_data,
                request.org_id,
                request.task_id
            )
            
            if response.status == "error":
                raise HTTPException(status_code=500, detail=response.error)
            
            return response
        
        @app.get("/tasks")
        async def list_tasks():
            """List available tasks"""
            return {
                "agent_id": self.agent_id,
                "tasks": list(self.tasks.keys())
            }
