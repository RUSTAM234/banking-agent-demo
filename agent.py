import os
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv()


def get_weather(city: str):
    """Get weather for a given city.
    Return the temperature_fahrenheit value in Fahrenheit label for locations such as US, Liberia, Burma"""
    api_key = os.getenv("WEATHER_API_KEY")
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, 'units': 'metric'}
    response = requests.get(base_url, params=params)
    data = response.json()
    temperature_celsius = data['main']['temp']
    temperature_fahrenheit = temperature_celsius * 9 / 5 + 32
    return data, {'temperature_fahrenheit': temperature_fahrenheit}


def get_location():
    """Get user's current location. Use this when the user asks about weather."""

    from flask import session

    user_location = session.get('user_location')

    if not user_location:
        return "Unknown"

    lat = user_location['lat']
    lon = user_location['lon']

    response = requests.get(
        f'https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json',
        headers={
            'User-Agent': 'WeatherAssistant/1.0'
        },
        timeout=3
    )

    data = response.json()

    city = data['address'].get(
        'city',
        data['address'].get('town', 'Unknown')
    )

    country = data['address'].get('country', '')

    return f"{city}, {country}"


llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0.7)

system_prompt = """
You are a helpful weather assistant.
YOUR WORKFLOW:
1. If the user asks about weather WITHOUT specifying a location, you MUST:
   - First call get_location() to find their location
   - Then call get_weather(city) with that location
2. If the user provides a city, call get_weather(city) directly.
3. If the user's location is in US, Liberia, or Burma, only mention the temperature in Fahrenheit.
Otherwise, only mention the temperature in Celsius.
"""

connection = SqliteSaver.from_conn_string('checkpoints.db')
checkpointer = connection.__enter__()

agent = create_agent(
    model=llm,
    tools=[get_weather, get_location],
    system_prompt=system_prompt,
    checkpointer=checkpointer
)
