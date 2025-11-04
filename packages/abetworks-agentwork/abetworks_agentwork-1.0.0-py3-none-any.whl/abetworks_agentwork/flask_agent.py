
"""Flask agent implementation"""

from flask import request, jsonify
from typing import Dict, Any
from .base import BaseAgent, AgentResponse, AgentError


class FlaskAgent(BaseAgent):
    """Agent implementation for Flask applications"""
    
    def register_routes(self, app):
        """Register Flask routes for the agent"""
        
        @app.route("/health", methods=["GET"])
        def health():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "version": self.version
            })
        
        @app.route("/execute", methods=["POST"])
        def execute():
            """Main execution endpoint"""
            # Validate API key
            api_key = request.headers.get("X-API-Key")
            if not self.validate_api_key(api_key):
                return jsonify({"error": "Invalid API key"}), 401
            
            # Parse request data
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            org_id = data.get("org_id")
            task_name = data.get("task_name", "default")
            input_data = data.get("input_data", {})
            task_id = data.get("task_id")
            
            # Validate org_id
            try:
                self.validate_org_id(org_id)
            except AgentError as e:
                return jsonify({"error": str(e)}), 400
            
            # Execute task
            response = self.execute_task(task_name, input_data, org_id, task_id)
            
            status_code = 200 if response.status == "success" else 500
            return jsonify(response.model_dump()), status_code
        
        @app.route("/tasks", methods=["GET"])
        def list_tasks():
            """List available tasks"""
            return jsonify({
                "agent_id": self.agent_id,
                "tasks": list(self.tasks.keys())
            })
