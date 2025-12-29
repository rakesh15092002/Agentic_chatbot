import logging
from app.graph.langgraph_setup import graph 
from app.services.thread_service import save_message
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver 

logger = logging.getLogger(__name__)

async def stream_chat_response(message: str, thread_id: str):
    """
    Stream chat response using LangGraph agent with tools.
    The agent will decide whether to use RAG or other tools.
    """
    
    config = {
        "configurable": {"thread_id": thread_id},
        "metadata": {"thread_id": thread_id, "run_name": "chat_stream"}
    }
    
    # Create the message object - NO RAG augmentation here
    input_message = HumanMessage(content=message)
    full_response = ""

    # 1. Save User Message to DB
    save_message(thread_id, "user", message)

    # 2. Open Async Database Connection
    async with AsyncSqliteSaver.from_conn_string("chatbot.db") as checkpointer:
        
        # 3. Compile the graph with checkpointer
        chatbot = graph.compile(checkpointer=checkpointer)

        # 4. Stream events
        async for event in chatbot.astream_events(
            {"messages": [input_message]}, 
            config=config, 
            version="v1"
        ):
            kind = event["event"]
            
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = chunk.content if hasattr(chunk, "content") else str(chunk)
                
                if content:
                    full_response += content
                    yield content

    # 5. Save the Full AI Response to DB
    save_message(thread_id, "assistant", full_response)