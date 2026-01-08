import logging
from app.graph.langgraph_setup import graph 
from app.services.thread_service import save_message
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver 

logger = logging.getLogger(__name__)

async def stream_chat_response(message: str, thread_id: str):
    """Stream chat response using LangGraph agent with tools."""
    
    config = {
        "configurable": {"thread_id": thread_id},
        "metadata": {"thread_id": thread_id, "run_name": "chat_stream"}
    }
    
    input_message = HumanMessage(content=message)
    full_response = ""

    # Save User Message to DB
    save_message(thread_id, "user", message)

    try:
        # Open Async Database Connection
        async with AsyncSqliteSaver.from_conn_string("chatbot.db") as checkpointer:
            
            # Compile the graph with checkpointer
            chatbot = graph.compile(checkpointer=checkpointer)

            # Stream events
            async for event in chatbot.astream_events(
                {"messages": [input_message]}, 
                config=config, 
                version="v1"
            ):
                kind = event["event"]
                
                # Stream LLM response chunks
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    content = chunk.content if hasattr(chunk, "content") else str(chunk)
                    
                    if content:
                        full_response += content
                        yield content
                
                # Log tool calls for debugging
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    logger.info(f"Tool called: {tool_name}")
                
                # Log tool results
                elif kind == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    logger.info(f"Tool finished: {tool_name}")

        # Save the Full AI Response to DB
        if full_response.strip():
            save_message(thread_id, "assistant", full_response)
        
    except Exception as e:
        logger.error(f"Error in stream_chat_response: {str(e)}")
        error_message = f"Error: {str(e)}"
        save_message(thread_id, "assistant", error_message)
        yield error_message