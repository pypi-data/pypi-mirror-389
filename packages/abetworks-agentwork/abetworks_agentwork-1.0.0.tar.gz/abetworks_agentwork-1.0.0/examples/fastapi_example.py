
"""Example FastAPI agent using abetworks-agentwork SDK"""

from abetworks_agentwork import FastAPIAgent, AgentResponse
from fastapi import FastAPI
import os

app = FastAPI(title="Data Processor Agent")

# Initialize agent
agent = FastAPIAgent(
    agent_id="data-processor",
    name="Data Processor",
    api_key=os.getenv("ABETWORKS_API_KEY", "development-key"),
    description="Processes and transforms data"
)

# Define tasks
@agent.task("transform")
async def transform_data(input_data, org_id, task_id):
    """Transform data according to rules"""
    data = input_data.get("data", [])
    operation = input_data.get("operation", "uppercase")
    
    if operation == "uppercase":
        result = [str(item).upper() for item in data]
    elif operation == "lowercase":
        result = [str(item).lower() for item in data]
    elif operation == "reverse":
        result = list(reversed(data))
    else:
        result = data
    
    return AgentResponse(
        status="success",
        output={
            "original": data,
            "transformed": result,
            "operation": operation
        },
        metadata={
            "org_id": org_id,
            "items_processed": len(data)
        }
    )

@agent.task("validate")
async def validate_data(input_data, org_id, task_id):
    """Validate data against schema"""
    data = input_data.get("data", {})
    required_fields = input_data.get("required_fields", [])
    
    missing_fields = [field for field in required_fields if field not in data]
    is_valid = len(missing_fields) == 0
    
    return AgentResponse(
        status="success",
        output={
            "is_valid": is_valid,
            "missing_fields": missing_fields,
            "data": data
        }
    )

# Register routes
agent.register_routes(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
