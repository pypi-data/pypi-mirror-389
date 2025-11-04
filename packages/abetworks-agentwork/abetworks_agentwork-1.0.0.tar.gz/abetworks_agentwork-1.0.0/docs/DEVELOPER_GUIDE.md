
# Abetworks AgentWork Developer Guide

## Building Your First Agent

### 1. Install the SDK

```bash
pip install abetworks-agentwork[flask]  # or [fastapi]
```

### 2. Create Your Agent

**Flask Example:**
```python
from abetworks_agentwork import FlaskAgent, AgentResponse
from flask import Flask

app = Flask(__name__)
agent = FlaskAgent(
    agent_id="my-agent",
    name="My Agent",
    api_key="your-api-key"
)

@agent.task("process")
def process(input_data, org_id, task_id):
    result = {"data": input_data}
    return AgentResponse(status="success", output=result)

agent.register_routes(app)
app.run(host="0.0.0.0", port=8000)
```

### 3. Deploy Your Agent

Deploy to Replit or any hosting service. Make sure it's accessible at a public URL.

### 4. Register with Abetworks

```python
from abetworks_agentwork import AbetworksClient

client = AbetworksClient(
    base_url="https://your-abetworks-instance.com",
    api_key="your-jwt-token"
)

client.register_agent(
    agent_id="my-agent",
    name="My Agent",
    description="Does amazing things",
    backend_endpoint="https://your-agent.repl.co",
    category="automation",
    icon="🚀"
)
```

## Multi-Tenant Best Practices

Always use the `org_id` parameter to isolate data:

```python
@agent.task("get_data")
def get_data(input_data, org_id, task_id):
    # ✅ CORRECT - Filter by org_id
    data = database.query(f"SELECT * FROM data WHERE org_id = '{org_id}'")
    
    # ❌ WRONG - No org_id filter
    # data = database.query("SELECT * FROM data")
    
    return AgentResponse(status="success", output={"data": data})
```

## Advanced Features

### Custom Task Handlers

```python
@agent.task("complex_task")
def complex_task(input_data, org_id, task_id):
    try:
        # Your complex logic here
        step1 = process_step1(input_data)
        step2 = process_step2(step1)
        
        return AgentResponse(
            status="success",
            output={"result": step2},
            metadata={"steps_completed": 2}
        )
    except Exception as e:
        return AgentResponse(
            status="error",
            error=str(e)
        )
```

### Using External APIs

```python
import requests

@agent.task("fetch_external")
def fetch_external(input_data, org_id, task_id):
    url = input_data.get("url")
    response = requests.get(url)
    
    return AgentResponse(
        status="success",
        output={"data": response.json()},
        metadata={"status_code": response.status_code}
    )
```

## Testing Your Agent

```python
# Test locally
response = agent.execute_task(
    task_name="process",
    input_data={"test": "data"},
    org_id="test-org-id",
    task_id="test-task-123"
)

print(response.status)  # "success"
print(response.output)  # {"data": {"test": "data"}}
```

## Publishing to PyPI

1. Update version in `setup.py`
2. Build: `python -m build`
3. Upload: `twine upload dist/*`

## Support

- GitHub: https://github.com/yourusername/abetworks-agentwork
- Docs: https://docs.abetworks.com
- Issues: https://github.com/yourusername/abetworks-agentwork/issues
