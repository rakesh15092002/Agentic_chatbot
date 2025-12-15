from fastapi import APIRouter
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.chat_service import send_message

router = APIRouter()

@router.post("/send", response_model=ChatResponse)
def chat_send(request: ChatRequest):
    """
    Send message to chatbot with thread support
    """
    reply = send_message(request.thread_id, request.message)
    return {"reply": reply, "thread_id": request.thread_id}
