import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.memory_agent import create_memory_agent
from dotenv import load_dotenv

load_dotenv()

def main():
    """Demonstrate memory capabilities of LangGraph agents."""
    print("=== LangGraph Memory Agent Demo ===\n")
    
    # Create agent with memory
    agent = create_memory_agent()
    
    # Configure thread for conversation continuity
    config = {"configurable": {"thread_id": "user_session_001"}}
    
    # Conversation flow
    conversation = [
        "Hi! My name is Alice and I'm interested in weather.",
        "What's the weather like in Seattle?",
        "Can you remind me what my name is?",
        "What city did I just ask about?",
        "Now tell me about the weather in Miami."
    ]
    
    print("Starting conversation with memory agent...\n")
    
    for i, message in enumerate(conversation, 1):
        print(f"User ({i}): {message}")
        response = agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config
        )
        print(f"Agent ({i}): {response['messages'][-1].content}\n")
        print("-" * 60 + "\n")
    
    print("Conversation complete! The agent maintained context throughout.")

if __name__ == "__main__":
    main()
