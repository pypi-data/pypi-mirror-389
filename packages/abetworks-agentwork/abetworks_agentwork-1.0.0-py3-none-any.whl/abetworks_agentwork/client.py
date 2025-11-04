
"""Client for communicating with Abetworks platform"""

import requests
from typing import Dict, Any, Optional


class AbetworksClient:
    """Client for interacting with Abetworks API"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def register_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        agent_type: str = "custom",
        category: str = "automation",
        icon: str = "🤖",
        backend_endpoint: str = "",
        price: int = 0,
        config_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register an agent with the Abetworks platform"""
        
        payload = {
            "id": agent_id,
            "name": name,
            "type": agent_type,
            "description": description,
            "icon": icon,
            "category": category,
            "backendEndpoint": backend_endpoint,
            "price": price,
        }
        
        if config_schema:
            payload["configSchema"] = config_schema
        
        response = requests.post(
            f"{self.base_url}/api/agents/register",
            json=payload,
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()
    
    def send_log(self, org_id: str, message: str, response: str = ""):
        """Send a log entry to Abetworks"""
        payload = {
            "org_id": org_id,
            "message": message,
            "response": response
        }
        
        requests.post(
            f"{self.base_url}/api/logs",
            json=payload,
            headers=self.headers
        )
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[str] = None
    ):
        """Update task status in Abetworks"""
        payload = {"status": status}
        if result:
            payload["result"] = result
        
        requests.patch(
            f"{self.base_url}/api/tasks/{task_id}",
            json=payload,
            headers=self.headers
        )
