
# Abetworks AgentWork SDK

Build AI agents for the Abetworks platform with Python. This SDK provides everything you need to create Flask or FastAPI agents that integrate seamlessly with Abetworks.

## Installation

```bash
# Basic installation
pip install abetworks-agentwork

# With Flask support
pip install abetworks-agentwork[flask]

# With FastAPI support
pip install abetworks-agentwork[fastapi]

# With all frameworks
pip install abetworks-agentwork[all]
```

## Quick Start

### Flask Agent

```python
from abetworks_agentwork import FlaskAgent, AgentResponse
from flask import Flask

app = Flask(__name__)
agent = FlaskAgent(
    agent_id="my-custom-agent",
    name="My Custom Agent",
    api_key="your-abetworks-api-key"
)

@agent.task("process_data")
def process_data(input_data, org_id, task_id):
    # Your agent logic here
    result = {"processed": input_data.get("text", "").upper()}
    return AgentResponse(
        status="success",
        output=result,
        metadata={"chars_processed": len(input_data.get("text", ""))}
    )

# Register routes with Flask
agent.register_routes(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### FastAPI Agent

```python
from abetworks_agentwork import FastAPIAgent, AgentResponse
from fastapi import FastAPI

app = FastAPI()
agent = FastAPIAgent(
    agent_id="my-custom-agent",
    name="My Custom Agent",
    api_key="your-abetworks-api-key"
)

@agent.task("analyze_sentiment")
async def analyze_sentiment(input_data, org_id, task_id):
    text = input_data.get("text", "")
    # Your NLP logic here
    sentiment = "positive" if "good" in text.lower() else "neutral"
    
    return AgentResponse(
        status="success",
        output={"sentiment": sentiment, "text": text},
        metadata={"confidence": 0.95}
    )

# Register routes with FastAPI
agent.register_routes(app)
```

## Features

- 🔐 **Built-in Authentication**: Secure API key validation
- 🏢 **Multi-tenant Support**: Automatic org_id isolation
- ⚡ **Framework Flexibility**: Works with Flask or FastAPI
- 📝 **Type Safety**: Pydantic models for data validation
- 🔄 **Auto Registration**: Register your agent with Abetworks platform
- 📊 **Error Handling**: Standardized error responses
- 🧪 **Testing Utilities**: Built-in test helpers

## Agent Registration

Register your agent with the Abetworks platform:

```python
agent.register_with_platform(
    abetworks_url="https://your-abetworks-instance.com",
    description="Analyzes sentiment in customer feedback",
    category="analytics",
    icon="💬",
    price=0
)
```

## Documentation

- Full Documentation: [https://docs.abetworks.in](https://docs.abetworks.in)
- GitHub Repository: [https://github.com/abetworks/abetworks-agentwork](https://github.com/abetworks/abetworks-agentwork)
- Website: [https://abetworks.in](https://abetworks.in)

## Support

- Email: contact@abetworks.in
- Issues: [GitHub Issues](https://github.com/abetworks/abetworks-agentwork/issues)

## License

MIT License - see LICENSE file for details
