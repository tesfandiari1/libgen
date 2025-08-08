import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

load_dotenv()

class WeatherResponse(BaseModel):
    city: str
    conditions: str
    temperature: str
    recommendation: str

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"In {city}: Sunny, 72°F, perfect for outdoor activities!"

def create_structured_agent():
    """Create an agent that returns structured responses."""
    model = ChatAnthropic(
        model="claude-3-haiku-20240307",
        temperature=0,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    # For structured output, we'll use the model's with_structured_output method
    structured_model = model.with_structured_output(WeatherResponse)
    
    agent = create_react_agent(
        model=model,
        tools=[get_weather]
    )
    
    return agent, structured_model

if __name__ == "__main__":
    agent, structured_model = create_structured_agent()
    
    # Get agent response
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "What's the weather in Paris? Please provide a detailed report."}]}
    )
    
    # Parse to structured format
    last_message = response['messages'][-1].content
    
    # For demonstration, create a structured response
    try:
        structured_response = structured_model.invoke(
            f"Based on this weather information: '{last_message}', provide a structured weather report for the city mentioned."
        )
        print("Structured Response:", structured_response)
    except Exception as e:
        print(f"Error creating structured response: {e}")
