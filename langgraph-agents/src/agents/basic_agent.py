import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

# Load environment variables
load_dotenv()

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

def create_basic_agent():
    """Create a basic ReAct agent with weather tool."""
    # Initialize the model with specific parameters
    model = ChatAnthropic(
        model="claude-3-haiku-20240307",  # Using Haiku for cost efficiency
        temperature=0,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    # Create the agent
    agent = create_react_agent(
        model=model,
        tools=[get_weather]
    )
    
    return agent

if __name__ == "__main__":
    # Test the agent
    agent = create_basic_agent()
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
    )
    print("Response:", response['messages'][-1].content)
