from typing import Dict, Any
import random

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    # Simulated weather data
    conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Clear"]
    temp = round(random.uniform(50, 85), 1)
    condition = random.choice(conditions)
    return f"Weather in {city}: {condition}, {temp}°F"

def get_stock_price(symbol: str) -> str:
    """Get the current stock price for a given symbol."""
    # Simulated stock price
    price = round(random.uniform(50, 500), 2)
    return f"${symbol} is currently trading at ${price}"

def search_web(query: str) -> str:
    """Search the web for information."""
    # Simulated web search
    return f"Search results for '{query}': Found relevant information about {query}."

def calculate(expression: str) -> str:
    """Perform mathematical calculations."""
    try:
        # Using a safer eval alternative for basic math
        # In production, use a proper math parser
        allowed_names = {
            k: v for k, v in __builtins__.items() 
            if k in ['abs', 'round', 'min', 'max', 'sum']
        }
        allowed_names.update({
            'pi': 3.14159265359,
            'e': 2.71828182846
        })
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"The result of {expression} is {result}"
    except:
        return "Invalid mathematical expression"

# Export all tools
AVAILABLE_TOOLS = [
    get_weather,
    get_stock_price,
    search_web,
    calculate
]
