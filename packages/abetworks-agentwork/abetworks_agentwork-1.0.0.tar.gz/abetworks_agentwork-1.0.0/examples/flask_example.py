
"""Example Flask agent using abetworks-agentwork SDK"""

from abetworks_agentwork import FlaskAgent, AgentResponse
from flask import Flask
import os

app = Flask(__name__)

# Initialize agent
agent = FlaskAgent(
    agent_id="sentiment-analyzer",
    name="Sentiment Analyzer",
    api_key=os.getenv("ABETWORKS_API_KEY", "development-key"),
    description="Analyzes sentiment in text"
)

# Define tasks
@agent.task("analyze")
def analyze_sentiment(input_data, org_id, task_id):
    """Analyze sentiment in text"""
    text = input_data.get("text", "")
    
    # Simple sentiment analysis (replace with real ML model)
    positive_words = ["good", "great", "excellent", "amazing", "love"]
    negative_words = ["bad", "terrible", "awful", "hate", "poor"]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return AgentResponse(
        status="success",
        output={
            "text": text,
            "sentiment": sentiment,
            "score": positive_count - negative_count
        },
        metadata={
            "org_id": org_id,
            "task_id": task_id,
            "chars_analyzed": len(text)
        }
    )

# Register routes
agent.register_routes(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
