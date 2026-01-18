from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from app.schemas.chat_schema import ChatRequest
from app.services.chat_service import stream_chat_response # Ensure ye updated wala imported ho
from app.utils.chat_title import generate_chat_title
from app.services.thread_service import update_thread_title
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def generate_and_save_title(thread_id: str, first_message: str):
    """
    This runs in the background. It will NOT stop or slow down the chat.
    """
    try:
        new_title = await generate_chat_title(first_message)
        logger.info(f"Generated Title for {thread_id}: {new_title}")
        update_thread_title(thread_id, new_title)
    except Exception as e:
        logger.error(f"Background Title Generation Failed: {e}")

@router.post("/send")
async def chat_send(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Stream chat response with RAG context & Tool use.
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not request.thread_id:
            raise HTTPException(status_code=400, detail="Thread ID is required")
        
        logger.info(f"Processing message for thread: {request.thread_id}")
        logger.info(f"Active Features: {request.features}") # Log features for debugging
        
        # Add Title Generation Task
        background_tasks.add_task(generate_and_save_title, request.thread_id, request.message)

        return StreamingResponse(
            # ✅ MAIN CHANGE: Pass 'features' to the service function
            stream_chat_response(
                message=request.message, 
                thread_id=request.thread_id, 
                features=request.features  # <-- Yahan features pass ho rahe hain
            ),
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