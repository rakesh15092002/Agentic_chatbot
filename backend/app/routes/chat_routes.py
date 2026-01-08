from fastapi import APIRouter, HTTPException, BackgroundTasks # ✅ ADDED BackgroundTasks
from fastapi.responses import StreamingResponse
from app.schemas.chat_schema import ChatRequest
from app.services.chat_service import stream_chat_response
# ✅ ADDED import for your title utility
from app.utils.chat_title import generate_chat_title
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ✅ NEW HELPER FUNCTION (Isolated, doesn't touch existing logic)
async def generate_and_save_title(thread_id: str, first_message: str):
    """
    This runs in the background. It will NOT stop or slow down the chat.
    """
    try:
        # 1. Generate Title
        new_title = await generate_chat_title(first_message)
        logger.info(f"Generated Title for {thread_id}: {new_title}")
        
        # 2. TODO: Add your DB save code here
        # await db.save_title(thread_id, new_title)
        
    except Exception as e:
        # If this fails, it just logs an error. The user still gets their chat response.
        logger.error(f"Background Title Generation Failed: {e}")

@router.post("/send")
async def chat_send(request: ChatRequest, background_tasks: BackgroundTasks): # ✅ ADDED parameter
    """
    Stream chat response with RAG context from Pinecone.
    """
    try:
        # --- EXISTING CODE (UNCHANGED) ---
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not request.thread_id:
            raise HTTPException(status_code=400, detail="Thread ID is required")
        
        logger.info(f"Processing message for thread: {request.thread_id}")
        # ---------------------------------
        
        # ✅ NEW: Add the task to the background queue
        # This line is instant. It does not wait for the title to be generated.
        background_tasks.add_task(generate_and_save_title, request.thread_id, request.message)

        # --- EXISTING CODE (UNCHANGED) ---
        return StreamingResponse(
            stream_chat_response(request.message, request.thread_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
        # ---------------------------------

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))