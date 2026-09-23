from flask import Flask, render_template, request, session, redirect, url_for
from agent import agent
import uuid

app = Flask(__name__)
app.secret_key = "you_secret_key"


@app.route('/')
def home():

    if 'thread_id' not in session:
        session['thread_id'] = str(uuid.uuid4())

    thread_id = session['thread_id']

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    messages = []

    try:
        state = agent.get_state(config)

        if state and state.values:

            agent_messages = state.values.get("messages", [])

            for msg in agent_messages:

                # -------------------------
                # HUMAN MESSAGE
                # -------------------------
                if msg.type == "human":

                    messages.append({
                        "type": "human",
                        "content": msg.content
                    })

                # -------------------------
                # AI MESSAGE
                # -------------------------
                elif msg.type == "ai":

                    content = msg.content

                    # Case 1:
                    # content = "Hello"
                    if isinstance(content, str):

                        if content.strip():
                            messages.append({
                                "type": "ai",
                                "content": content
                            })

                    # Case 2:
                    # content = [
                    #   {
                    #       "type": "text",
                    #       "text": "Hello"
                    #   }
                    # ]
                    elif isinstance(content, list):

                        text_parts = []

                        for item in content:

                            if isinstance(item, dict):

                                if item.get("type") == "text":
                                    text = item.get("text")

                                    if text:
                                        text_parts.append(text)

                        final_text = "\n".join(text_parts)

                        if final_text.strip():

                            messages.append({
                                "type": "ai",
                                "content": final_text
                            })

    except Exception as e:

        print("Error loading chat history:", e)

    return render_template(
        "chat.html",
        messages=messages
    )

@app.route('/send', methods=['POST'])
def send():

    user_message = request.form.get('message')

    user_lat = request.form.get('latitude')
    user_lon = request.form.get('longitude')

    # Store location in Flask session
    if user_lat and user_lon:

        session['user_location'] = {
            'lat': user_lat,
            'lon': user_lon
        }

    # Get current thread
    thread_id = session.get('thread_id')

    if not thread_id:
        thread_id = str(uuid.uuid4())
        session['thread_id'] = thread_id

    # IMPORTANT:
    # This thread_id tells LangGraph which conversation to continue
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    try:

        response = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            },
            config=config
        )

        print("Agent response:")
        content = response['messages'][-1].content

        if isinstance(content, list):
            print(content[0]["text"])
        else:
            print(content)

    except Exception as e:

        print("Agent error:", e)

    return redirect(url_for('home'))


@app.route('/clear')
def clear():

    # Generate a completely new conversation/thread
    session['thread_id'] = str(uuid.uuid4())

    # Remove previous location if required
    session.pop('user_location', None)

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)