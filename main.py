import os

from langchain.chat_models import init_chat_model

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

model = init_chat_model(
    model="gemini-3-flash-preview",
    model_provider="google-genai",
    api_key=GOOGLE_API_KEY)

# TODO: Change the prompt to "What is artificial intelligence in one sentence?"
with open("wood.txt") as file:
    wood = file.read()
response = model.invoke(f"hi,which of these is best for furniture?{wood}")

print(response.content[0]['text'])
