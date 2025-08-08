import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic

load_dotenv()

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

def create_memory_agent():
    """Create an agent with conversation memory."""
    model = ChatAnthropic(
        model="claude-3-haiku-20240307",
        temperature=0,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    # Create checkpointer for memory
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=model,
        tools=[get_weather],
        checkpointer=checkpointer
    )
    
    return agent

if __name__ == "__main__":
    agent = create_memory_agent()
    config = {"configurable": {"thread_id": "conversation_1"}}
    
    # First message
    response1 = agent.invoke(
        {"messages": [{"role": "user", "content": "What's the weather in SF?"}]},
        config
    )
    print("Response 1:", response1['messages'][-1].content)
    
    # Follow-up message (agent should remember context)
    response2 = agent.invoke(
        {"messages": [{"role": "user", "content": "What about New York?"}]},
        config
    )
    print("Response 2:", response2['messages'][-1].content)
