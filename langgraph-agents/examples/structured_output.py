import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.structured_agent import create_structured_agent, WeatherResponse
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import json

load_dotenv()

def main():
    """Demonstrate structured output capabilities."""
    print("=== LangGraph Structured Output Demo ===\n")
    
    # Create agent and structured model
    agent, structured_model = create_structured_agent()
    
    # Cities to check
    cities = ["London", "Tokyo", "New York", "Sydney"]
    
    print("Getting weather reports for multiple cities...\n")
    
    for city in cities:
        print(f"Checking weather for {city}:")
        print("-" * 40)
        
        # Get agent response
        response = agent.invoke(
            {"messages": [{"role": "user", "content": f"What's the weather in {city}? Give me a detailed report."}]}
        )
        
        agent_response = response['messages'][-1].content
        print(f"Agent Response: {agent_response}")
        
        # Try to get structured output
        try:
            # Create a more specific prompt for structured output
            structured_prompt = f"""
            Based on this weather information: "{agent_response}"
            
            Provide a structured weather report with:
            - city: {city}
            - conditions: current weather conditions
            - temperature: current temperature
            - recommendation: what activities are recommended
            """
            
            structured_response = structured_model.invoke(structured_prompt)
            print(f"\nStructured Output:")
            print(f"  City: {structured_response.city}")
            print(f"  Conditions: {structured_response.conditions}")
            print(f"  Temperature: {structured_response.temperature}")
            print(f"  Recommendation: {structured_response.recommendation}")
        except Exception as e:
            print(f"Could not generate structured output: {e}")
        
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    main()
