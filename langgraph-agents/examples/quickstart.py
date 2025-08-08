import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.basic_agent import create_basic_agent
from src.agents.memory_agent import create_memory_agent
from src.agents.structured_agent import create_structured_agent
from src.tools.custom_tools import AVAILABLE_TOOLS
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()

def main():
    print("=== LangGraph Agent Examples ===\n")
    
    # 1. Basic Agent
    print("1. Basic Agent Example:")
    print("-" * 40)
    basic_agent = create_basic_agent()
    response = basic_agent.invoke(
        {"messages": [{"role": "user", "content": "What's the weather in Tokyo?"}]}
    )
    print(f"Response: {response['messages'][-1].content}\n")
    
    # 2. Agent with Multiple Tools
    print("2. Multi-Tool Agent Example:")
    print("-" * 40)
    model = ChatAnthropic(
        model="claude-3-haiku-20240307", 
        temperature=0,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    multi_tool_agent = create_react_agent(
        model=model,
        tools=AVAILABLE_TOOLS
    )
    
    response = multi_tool_agent.invoke(
        {"messages": [{"role": "user", "content": "What's the stock price of AAPL and calculate 15% of it?"}]}
    )
    print(f"Response: {response['messages'][-1].content}\n")
    
    # 3. Memory Agent
    print("3. Memory Agent Example:")
    print("-" * 40)
    memory_agent = create_memory_agent()
    config = {"configurable": {"thread_id": "demo_session"}}
    
    response1 = memory_agent.invoke(
        {"messages": [{"role": "user", "content": "Remember that my favorite city is Barcelona"}]},
        config
    )
    print(f"First response: {response1['messages'][-1].content}")
    
    response2 = memory_agent.invoke(
        {"messages": [{"role": "user", "content": "What's the weather in my favorite city?"}]},
        config
    )
    print(f"Second response: {response2['messages'][-1].content}\n")

if __name__ == "__main__":
    main()
