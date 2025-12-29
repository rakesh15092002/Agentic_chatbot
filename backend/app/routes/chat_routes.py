from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.chat_schema import ChatRequest
from app.services.chat_service import stream_chat_response
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/send")
async def chat_send(request: ChatRequest):
    """
    Stream chat response with RAG context from Pinecone.
    
    Request body:
    {
        "message": "Your message here",
        "thread_id": "uuid-of-thread"
    }
    
    Returns: Server-Sent Events stream
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not request.thread_id:
            raise HTTPException(status_code=400, detail="Thread ID is required")
        
        logger.info(f"Processing message for thread: {request.thread_id}")
        
        return StreamingResponse(
            stream_chat_response(request.message, request.thread_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))