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

def simplify_schema(schema_def: Dict) -> Dict:
    """Simplify schema to avoid Groq API errors"""
    properties = schema_def.get("properties", {})
    simplified_properties = {}
    
    for prop_name, prop_info in properties.items():
        # Keep only essential fields for Groq
        simplified_properties[prop_name] = {
            "type": prop_info.get("type", "string"),
            "description": prop_info.get("description", "")[:200]  # Limit description length
        }
        
        # Add enum if present and not too large
        if "enum" in prop_info and len(prop_info["enum"]) <= 10:
            simplified_properties[prop_name]["enum"] = prop_info["enum"]
    
    return {
        "type": "object",
        "properties": simplified_properties,
        "required": schema_def.get("required", [])
    }

def create_tool_schema(tool_name: str, schema_def: Dict) -> Type[BaseModel]:
    """Create Pydantic schema for tool validation"""
    fields = {}
    properties = schema_def.get("properties", {})
    required_fields = schema_def.get("required", [])
    
    for prop_name, prop_info in properties.items():
        description = prop_info.get("description", "")[:200]  # Limit description
        prop_type = prop_info.get("type", "string")
        
        # Map JSON schema types to Python types
        if prop_type == "string":
            field_type = str
        elif prop_type == "integer":
            field_type = int
        elif prop_type == "boolean":
            field_type = bool
        elif prop_type == "array":
            field_type = list
        elif prop_type == "object":
            field_type = dict
        else:
            field_type = Any
        
        # Make field optional if not required
        if prop_name in required_fields:
            fields[prop_name] = (field_type, Field(description=description))
        else:
            fields[prop_name] = (Optional[field_type], Field(default=None, description=description))

    return create_model(f"{tool_name}Input", **fields)

async def stream_chat_response(message: str, thread_id: str, features: dict = {}):
    """
    Stream chat response using LangGraph agent with tools.
    """
    mcp_client = None
    converted_mcp_tools = []
    tool_names_list = []

    # Setup MCP Client if GitHub feature is enabled
    if features.get("github", False):
        try:
            logger.info("🔌 Connecting to GitHub MCP...")
            mcp_client = GitHubMCPClient()
            await mcp_client.connect()
            mcp_tool_defs = await mcp_client.list_tools()

            # ✅ CRITICAL FIX: Only load essential GitHub tools to save tokens
            ALLOWED_TOOLS = [
                "search_repositories",
                "get_file_contents", 
                "list_commits",
                "get_issue",
                "create_repository"
            ]

            for tool_def in mcp_tool_defs:
                tool_name = tool_def["function"]["name"]
                
                # Skip tools not in whitelist
                if tool_name not in ALLOWED_TOOLS:
                    logger.debug(f"⏭️ Skipping tool: {tool_name}")
                    continue
                
                tool_desc = tool_def["function"]["description"][:300]  # Limit description
                input_schema = tool_def["function"]["parameters"]
                
                # Simplify schema for Groq compatibility
                simplified_schema = simplify_schema(input_schema)

                # Create schema
                args_schema = create_tool_schema(tool_name, simplified_schema)
                
                # Create wrapper function with proper closure
                def make_wrapper(client, name):
                    async def wrapper(**kwargs):
                        logger.info(f"⚡ Executing Tool: {name} with args: {kwargs}")
                        try:
                            result = await client.call_tool(name, kwargs)
                            logger.info(f"✅ Tool {name} returned: {result[:200]}...")
                            return result
                        except Exception as e:
                            error_msg = f"Error executing {name}: {str(e)}"
                            logger.error(error_msg)
                            return error_msg
                    return wrapper
                
                tool_obj = StructuredTool.from_function(
                    func=None,
                    coroutine=make_wrapper(mcp_client, tool_name),
                    name=tool_name,
                    description=tool_desc,
                    args_schema=args_schema
                )
                converted_mcp_tools.append(tool_obj)
                tool_names_list.append(tool_name)
                
            logger.info(f"✅ Loaded {len(tool_names_list)} GitHub Tools: {tool_names_list}")

        except Exception as e:
            logger.error(f"❌ GitHub Connection Error: {e}", exc_info=True)
            yield f"⚠️ GitHub Connection Failed: {str(e)}\n\n"

    # Configuration
    config = {
        "configurable": {
            "thread_id": thread_id,
            "mcp_tools": converted_mcp_tools 
        },
        "metadata": {"thread_id": thread_id}
    }
    
    # Prepare user message
    input_message = HumanMessage(content=message)
    
    # Save original message to DB
    save_message(thread_id, "user", message)

    full_response = ""

    # Execute with LangGraph
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
                    tool_name = event.get("name", "unknown")
                    logger.info(f"🛠️ Tool Started: {tool_name}")
                
                elif kind == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    logger.info(f"✅ Tool Completed: {tool_name}")
        
        # Save assistant response
        if full_response.strip():
            save_message(thread_id, "assistant", full_response)
        
    except Exception as e:
        logger.error(f"🚨 Chat Error: {str(e)}", exc_info=True)
        error_message = f"\n\nError: {str(e)}"
        full_response += error_message
        yield error_message

    finally:
        # Close MCP connection
        if mcp_client:
            try:
                await mcp_client.close()
                logger.info("🔌 GitHub MCP connection closed")
            except Exception as e:
                logger.error(f"Error closing MCP client: {e}")