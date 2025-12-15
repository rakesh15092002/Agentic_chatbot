from app.graph.langgraph_setup import chatbot
from app.services.thread_service import save_message, get_thread_messages
from langchain_core.messages import HumanMessage

def send_message(thread_id: str, user_message: str) -> str:
    """
    Sends user message to LangGraph, maintains thread context,
    saves user and AI messages in DB, returns AI reply
    """

    # 1️⃣ Fetch all previous messages for this thread
    messages = get_thread_messages(thread_id)

    # 2️⃣ Add current user message
    messages.append(HumanMessage(content=user_message))

    # 3️⃣ Invoke LangGraph with full state
    state = {"messages": messages}
    response_state = chatbot.invoke(state)
    ai_message = response_state["messages"][-1]

    # 4️⃣ Save messages in DB
    save_message(thread_id, "user", user_message)
    save_message(thread_id, "assistant", ai_message.content)

    return ai_message.content
