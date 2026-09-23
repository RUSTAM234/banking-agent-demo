import requests
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver


load_dotenv()


def get_weather(city: str):
    """Get weather for a given city."""

    api_key = os.getenv("WEATHER_API_KEY")

    base_url = "http://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": api_key,
        "units": "imperial"
    }

    response = requests.get(base_url, params=params)

    data = response.json()

    temperature_fahrenheit = data["main"]["temp"]

    return {
        "temperature_fahrenheit": temperature_fahrenheit,
        "condition": data["weather"][0]["description"],
        "wind_speed": data["wind"]["speed"]
    }


def get_location():
    """Get user's current location."""

    response = requests.get(
        "https://ipapi.co/json/",
        headers={"User-agent": "your-bot 0.1"}
    )

    data = response.json()

    city = data["city"]
    country = data.get("country_name")

    return f"{city}, {country}"


llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0.7,
)


system_prompt = """
You are a helpful weather assistant.

YOUR WORKFLOW:

1. If the user asks about weather WITHOUT specifying a location:
   - First call get_location()
   - Then call get_weather(city) with that location.

2. If the user provides a city:
   - Call get_weather(city) directly.

3. Use your knowledge to determine which temperature unit
   is standard for the given location.

4. Present weather information including temperature,
   condition, wind speed, and other relevant details.
"""


agent = create_agent(
    model=llm,
    tools=[get_weather, get_location],
    system_prompt=system_prompt,
    checkpointer=InMemorySaver()
)

while True:
    if __name__ == "__main__":

        # First question
        user_query = input("Enter your query: ")
        if user_query in ['bye' , 'exit', 'quit']:
             break

        response1 = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_query
                    }
                ]
            },
            {
                "configurable": {
                    "thread_id": "1"
                }
            }
        )

        content = response1["messages"][-1].content

        if isinstance(content, list):
            print(content[0]["text"])
        else:
            print(content)


        # # Second question
        # user_query2 = input("Enter your query: ")
        #
        # response2 = agent.invoke(
        #     {
        #         "messages": [
        #             {
        #                 "role": "user",
        #                 "content": user_query2
        #             }
        #         ]
        #     },
        #     {
        #         "configurable": {
        #             "thread_id": "1"
        #         }
        #     }
        # )
        #
        # content = response2["messages"][-1].content
        #
        # if isinstance(content, list):
        #     print(content[0]["text"])
        # else:
        #     print(content)