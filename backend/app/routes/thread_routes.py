from fastapi import APIRouter, HTTPException
from app.services.thread_service import (
    create_thread, 
    get_threads, 
    get_thread_messages_for_api, 
    delete_thread
)

router = APIRouter()

# 1. Create a new thread
# Final URL: http://localhost:8000/thread/create
@router.post("/create")
def create_thread_api(name: str = "New Chat"):
    thread_id = create_thread(name)
    return {"thread_id": thread_id, "name": name}

# 2. List all threads
# Final URL: http://localhost:8000/thread/all
@router.get("/all")
def list_threads_api():
    return get_threads()

# 3. Get all messages for a specific thread
# Final URL: http://localhost:8000/thread/{thread_id}/messages
@router.get("/{thread_id}/messages")
def get_thread_messages_api(thread_id: str):
    messages = get_thread_messages_for_api(thread_id)
    return {"thread_id": thread_id, "messages": messages}

# 4. Delete a thread (NEW)
# Final URL: http://localhost:8000/thread/{thread_id}
@router.delete("/{thread_id}")
def delete_thread_api(thread_id: str):
    try:
        delete_thread(thread_id)
        return {"success": True, "message": "Thread deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))