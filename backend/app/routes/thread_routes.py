from fastapi import APIRouter
from app.services.thread_service import create_thread, get_threads, get_thread_messages_for_api

router = APIRouter()

# Create a new thread
@router.post("/thread/create")
def create_thread_api(name: str = "New Chat"):
    thread_id = create_thread(name)
    return {"thread_id": thread_id, "name": name}

# List all threads
@router.get("/all")
def list_threads_api():
    return get_threads()

# Get all messages for a specific thread
@router.get("/thread/{thread_id}/messages")
def get_thread_messages_api(thread_id: str):
    messages = get_thread_messages_for_api(thread_id)
    return {"thread_id": thread_id, "messages": messages}
