import requests
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.agents import create_agent

load_dotenv()


def get_weather(city: str):
    """Get weather for a given city.
    Return the temperature_fahrenheit value in Fahrenheit label for locations such as US, Liberia, Burma"""
    # TODO: Change "WEATHER_API_KEY" to "OPENWEATHER_API_KEY"
    api_key = os.getenv("WEATHER_API_KEY")
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    # TODO: Change 'imperial' to 'metric'
    params = {
        "q": city,
        "appid": api_key,
        'units': 'imperial'
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    temperature_celsius = data['main']['temp']
    temperature_fahrenheit = temperature_celsius * 9 / 5 + 32
    return data, {'temperature_fahrenheit': temperature_fahrenheit}


def get_location():
    """Get user's current location. Use this when the user asks about weather."""
    response = requests.get("https://ipapi.co/json/", headers={'User-agent': 'your-bot 0.1'})
    data = response.json()
    city = data['city']
    country = data.get('country_name')
    return f"{city}, {country}"


llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0.7,
)

system_prompt = """
You are a helpful weather assistant.
YOUR WORKFLOW:
1. If the user asks about weather WITHOUT specifying a location, you MUST:
   - First call get_location() to find their location
   - Then call get_weather(city) with that location

2. If the user provides a city, call get_weather(city) directly.

3. Use your knowledge to determine which temperature unit is standard for the given location.

4. Present the weather information including temperature, condition, wind speed, and any other relevant details.
"""

agent = create_agent(
    model=llm,
    tools=[get_weather, get_location],
    system_prompt=system_prompt
)

if __name__ == "__main__":
    user_query = input("Enter your query: ")
    response = agent.invoke(
        {"messages": [{'role': 'user', 'content': user_query}]})
    # print(response['messages'][-1].content)

    content = response['messages'][-1].content

    if isinstance(content, list):
        print(content[0]["text"])
    else:
        print(content)
