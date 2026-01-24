import logging
from typing import Any, Dict, List, Optional, Type
from pydantic import create_model, Field, BaseModel
from app.graph.langgraph_setup import graph 
from app.services.thread_service import save_message
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver 
from langchain_core.tools import StructuredTool 
from app.services.mcp_manager import GitHubMCPClient

logger = logging.getLogger(__name__)

# ==========================================
# 1. SCHEMA CONVERTER
# ==========================================
def create_tool_schema(tool_name: str, schema_def: Dict) -> Type[BaseModel]:
    """
    Converts JSON Schema to Pydantic Model.
    """
    fields = {}
    properties = schema_def.get("properties", {})
    required_fields = schema_def.get("required", [])
    
    for prop_name, prop_info in properties.items():
        desc = prop_info.get("description", "")[:200]
        json_type = prop_info.get("type", "string")
        
        # Map JSON types to Python
        if json_type == "integer": python_type = int
        elif json_type == "number": python_type = float
        elif json_type == "boolean": python_type = bool
        elif json_type == "array": python_type = list
        elif json_type == "object": python_type = dict
        else: python_type = str

        if prop_name in required_fields:
            fields[prop_name] = (python_type, Field(description=desc))
        else:
            # Set smart defaults to help the AI
            default_val = None
            if prop_name == "page": default_val = 1
            if prop_name == "perPage": default_val = 10
            
            fields[prop_name] = (Optional[python_type], Field(default=default_val, description=desc))

    return create_model(f"{tool_name}Input", **fields)

# ==========================================
# 2. STREAM CHAT SERVICE
# ==========================================
async def stream_chat_response(message: str, thread_id: str, features: dict = {}):
    """
    Stream chat response using LangGraph agent with GitHub MCP tools.
    """
    mcp_client = None
    converted_mcp_tools = []
    
    # --- LOAD GITHUB TOOLS ---
    if features.get("github", False):
        try:
            logger.info("🔌 Connecting to GitHub MCP...")
            mcp_client = GitHubMCPClient()
            await mcp_client.connect()
            mcp_tool_defs = await mcp_client.list_tools()

            # Allowed tools whitelist
            ALLOWED_TOOLS = [
                "search_repositories",
                "get_file_contents", 
                "list_commits",
                "list_issues"
            ]

            for tool_def in mcp_tool_defs:
                tool_name = tool_def["function"]["name"]
                
                if tool_name in ALLOWED_TOOLS:
                    # -------------------------------------------------
                    # ✅ THE UNIVERSAL FIX: CLEAN WRAPPER
                    # -------------------------------------------------
                    def make_wrapper(client, name):
                        async def wrapper(**kwargs):
                            try:
                                # 1. Remove 'None' values. GitHub crashes on 'null', so we just remove the key.
                                clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
                                
                                logger.info(f"⚡ Executing {name} with args: {clean_kwargs}")
                                
                                result = await client.call_tool(name, clean_kwargs)
                                return str(result)[:3000] 
                            except Exception as e:
                                error_msg = f"GitHub Tool Error: {str(e)}"
                                logger.error(error_msg)
                                return error_msg
                        return wrapper
                    # -------------------------------------------------

                    schema_def = tool_def["function"]["parameters"]
                    args_schema = create_tool_schema(tool_name, schema_def)
                    
                    tool_obj = StructuredTool.from_function(
                        func=None,
                        coroutine=make_wrapper(mcp_client, tool_name),
                        name=tool_name,
                        description=tool_def["function"]["description"][:300],
                        args_schema=args_schema
                    )
                    converted_mcp_tools.append(tool_obj)
            
            logger.info(f"✅ Loaded {len(converted_mcp_tools)} GitHub tools")

        except Exception as e:
            logger.error(f"❌ GitHub connection failed: {e}")
            yield f"⚠️ GitHub Error: {str(e)}\n\n"

    # --- CONFIG ---
    config = {
        "configurable": {
            "thread_id": thread_id,
            "mcp_tools": converted_mcp_tools 
        },
        "recursion_limit": 15
    }
    
    input_message = HumanMessage(content=message)
    save_message(thread_id, "user", message)

    full_response = ""

    # --- EXECUTE ---
    try:
        async with AsyncSqliteSaver.from_conn_string("chatbot.db") as checkpointer:
            chatbot = graph.compile(checkpointer=checkpointer)

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
                
                elif kind == "on_tool_start":
                    logger.info(f"🛠️ Tool Requested: {event.get('name')}")

        if full_response.strip():
            save_message(thread_id, "assistant", full_response)
        
    except Exception as e:
        logger.error(f"🚨 Chat Error: {e}", exc_info=True)
        yield f"\n\n❌ Error: {str(e)}"

    finally:
        if mcp_client:
            await mcp_client.close()