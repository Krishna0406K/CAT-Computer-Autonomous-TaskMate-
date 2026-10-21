"""
Example Plugin: Weather Tool
Drop this in the `plugins/` directory and CAT will automatically learn it!
"""

import httpx

def get_current_weather(city: str) -> str:
    """
    Fetches the current weather for a specified city using the free wttr.in API.
    Use this tool whenever the user asks for the weather.
    """
    try:
        # wttr.in is a fantastic open source weather API that returns plain text!
        url = f"https://wttr.in/{city}?format=3"
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        return f"Error fetching weather for {city}: {str(e)}"

# 1. EXPORT TOOLS: Add your functions to this list so CAT can see them.
CAT_TOOLS = [get_current_weather]

# 2. ASSIGN RISKS: (Optional) Tell CAT's Permission Engine how dangerous this tool is.
# If omitted, it defaults to CRITICAL (requires user approval).
CAT_RISKS = {
    "get_current_weather": "LOW" 
}
