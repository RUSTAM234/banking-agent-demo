from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv()


def get_weather(city: str):
    """Get weather for a given city"""
    return {'condition': 'sunny', 'temperature': 25}


def get_location():
    """Get user's current location. Use this when the user asks about weather."""
    return "Rome, Italy"


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
"""

with SqliteSaver.from_conn_string('checkpoints.db') as checkpointer:
    agent = create_agent(
        model=llm,
        tools=[get_weather, get_location],
        system_prompt=system_prompt,
        checkpointer=checkpointer
    )

    while True:
        user_query = input("Enter your query: ")
        if user_query in ['bye', 'quit', 'exit']:
            break
        response = agent.invoke(
            {"messages": [{'role': 'user', 'content': user_query}]},
            {"configurable": {"thread_id": "1"}}
        )

        # TODO: loop over response['messages']; print 'You: ' + content for human messages, 'Agent: ' + content for ai messages with non-empty content

        print(response['messages'][-1].content)
