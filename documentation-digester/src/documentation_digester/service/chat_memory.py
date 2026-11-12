
from langchain_core.chat_history import InMemoryChatMessageHistory


# Store conversation histories while the application is running.
# Each session ID has its own separate conversation history.
chat_histories = {}

# Remember the last 10 question-and-answer pairs.
MAX_TURNS = 10


# Get the conversation history for a particular session.
def get_session_history(session_id: str) -> InMemoryChatMessageHistory:

    # If this is a new conversation, create an empty history.
    if session_id not in chat_histories:
        chat_histories[session_id] = InMemoryChatMessageHistory()

    # Return the existing or newly created history.
    return chat_histories[session_id]


# Save the user's question and the chatbot's answer.
def save_conversation(session_id: str, question: str, answer: str):

    # Find the conversation belonging to this session.
    history = get_session_history(session_id)

    # Store the user's question.
    history.add_user_message(question)

    # Store the chatbot's response.
    history.add_ai_message(answer)

    # Each turn contains 2 messages: question and answer.
    # Keep only the 3 most recent turns (6 messages).
    history.messages = history.messages[-MAX_TURNS * 2:]
