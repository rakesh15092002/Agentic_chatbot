from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from app.schemas.chat_schema import ChatRequest
from app.services.chat_service import stream_chat_response 
from app.utils.chat_title import generate_chat_title
# ✅ FIX: Import the function that ACTUALLY exists in your service
from app.services.thread_service import update_thread_title, get_thread_messages_for_api 
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def generate_and_save_title(thread_id: str, first_message: str):
    """
    This runs in the background to generate a title for new chats.
    """
    try:
        new_title = await generate_chat_title(first_message)
        logger.info(f"📝 Generated Title for {thread_id}: {new_title}")
        update_thread_title(thread_id, new_title)
    except Exception as e:
        logger.error(f"Background Title Generation Failed: {e}")

@router.post("/send")
async def chat_send(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Stream chat response. 
    Checks history first: if empty, generates a title. If not empty, keeps existing title.
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not request.thread_id:
            raise HTTPException(status_code=400, detail="Thread ID is required")
        
        logger.info(f"Processing message for thread: {request.thread_id}")

        # ---------------------------------------------------------
        # ✅ FIX: Check if this is a new conversation using your existing function
        # ---------------------------------------------------------
        try:
            # Fetch existing messages (returns a list of dicts)
            existing_messages = get_thread_messages_for_api(request.thread_id)
            
            # If list is empty, it's a brand new chat -> Generate Title
            if not existing_messages:
                logger.info("🆕 New conversation detected. Queueing title generation...")
                background_tasks.add_task(generate_and_save_title, request.thread_id, request.message)
            else:
                logger.info(f"⏩ Existing conversation ({len(existing_messages)} msgs). Skipping title gen.")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not check message history: {e}")
        # ---------------------------------------------------------

        return StreamingResponse(
            stream_chat_response(
                message=request.message, 
                thread_id=request.thread_id, 
                features=request.features 
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