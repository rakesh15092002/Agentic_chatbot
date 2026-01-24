import os
import logging
from typing import Annotated, TypedDict, Literal
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import trim_messages

# Import existing static tools
from app.utils.tools import tools as static_tools

logger = logging.getLogger(__name__)
load_dotenv()

# --- CONFIGURATION ---
MODEL_NAME = "llama-3.3-70b-versatile"

# 1. Main Model - Increased temperature for natural responses
llm = ChatGroq(
    model=MODEL_NAME,
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.4,  # ✅ Higher temp = more natural, less robotic
)

# 2. Fallback Model
llm_fallback = ChatGroq(
    model="llama-3.1-8b-instant", 
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,  # ✅ Still conservative but not frozen
)

# --- IMPROVED SYSTEM PROMPT ---
BASE_SYSTEM_PROMPT = """You are a friendly, helpful AI assistant. Respond naturally and conversationally.

**Personality:**
- Be warm and approachable
- For simple greetings like "hi" or "hello", respond casually (e.g., "Hey! How can I help you today?")
- For "how are you" questions, keep it brief and friendly (e.g., "I'm doing great, thanks! What can I do for you?")
- Don't be overly formal or mechanical
- Show personality while remaining professional

**Tool Usage:**
Use tools when you need specific information or capabilities:
- **duckduckgo_search**: Current events, news, general web information
- **calculator**: Mathematical calculations
- **get_stock_price**: Stock market data (ticker symbols)
- **get_weather**: Weather information for any city
- **search_documents**: Search uploaded PDF documents

**When GitHub tools are available:**
- **search_repositories**: Find GitHub repositories
- **get_file_contents**: Read files from repositories  
- **list_commits**: View commit history (always use perPage=10)
- **list_issues**: List repository issues

**Guidelines:**
- For casual conversation, just respond naturally without tools
- Use tools when you need current data or specific capabilities
- If a tool fails, acknowledge it and try to help anyway
- Don't announce you're using tools - just use them naturally
- Keep responses concise and helpful"""


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState, config):
    """Main chat node with safe dynamic tools."""
    messages = state["messages"]
    
    # 1. Get all available tools
    dynamic_tools = config.get("configurable", {}).get("mcp_tools", [])
    all_tools = static_tools + dynamic_tools
    
    # 2. Build dynamic system prompt with tool info
    if all_tools:
        tool_descriptions = "\n".join([f"  • {t.name}: {t.description[:100]}" for t in all_tools])
        sys_msg_content = f"{BASE_SYSTEM_PROMPT}\n\n**Available Tools:**\n{tool_descriptions}"
    else:
        sys_msg_content = BASE_SYSTEM_PROMPT
    
    sys_msg = SystemMessage(content=sys_msg_content)
    
    # Replace or prepend system message
    if messages and isinstance(messages[0], SystemMessage):
        messages[0] = sys_msg
    else:
        messages = [sys_msg] + messages

    # 3. Context Trimming - FIXED to use proper token counter
    try:
        trimmed_messages = trim_messages(
            messages,
            max_tokens=4000,  # ✅ Reduced to safe limit
            strategy="last",
            token_counter=llm,  # ✅ Use actual model tokenizer
            include_system=True,
            start_on="human"
        )
    except Exception as trim_error:
        logger.warning(f"⚠️ Trimming failed: {trim_error}, using last 15 messages")
        # Fallback: keep system message + last 15 messages
        trimmed_messages = [messages[0]] + messages[-15:] if len(messages) > 15 else messages

    # 4. Invoke LLM with tools
    try:
        if all_tools:
            # ✅ GOOD: parallel_tool_calls=False prevents crashes
            llm_with_tools = llm.bind_tools(all_tools, parallel_tool_calls=False)
            response = llm_with_tools.invoke(trimmed_messages)
        else:
            response = llm.invoke(trimmed_messages)
        
        return {"messages": [response]}
    
    except Exception as e:
        logger.error(f"⚠️ Primary LLM error: {type(e).__name__}: {str(e)[:200]}")
        logger.info("🔄 Attempting fallback model...")
        
        try:
            if all_tools:
                fallback_with_tools = llm_fallback.bind_tools(all_tools, parallel_tool_calls=False)
                response = fallback_with_tools.invoke(trimmed_messages)
            else:
                response = llm_fallback.invoke(trimmed_messages)
            
            return {"messages": [response]}
        
        except Exception as retry_error:
            logger.error(f"❌ Fallback failed: {type(retry_error).__name__}: {str(retry_error)[:200]}")
            return {"messages": [AIMessage(
                content="I'm having technical difficulties right now. Please try again in a moment."
            )]}


async def dynamic_tool_node(state: ChatState, config):
    """Executes tools with safety limits."""
    messages = state["messages"]
    last_message = messages[-1]
    
    dynamic_tools = config.get("configurable", {}).get("mcp_tools", [])
    all_tools = static_tools + dynamic_tools
    tool_map = {tool.name: tool for tool in all_tools}
    
    results = []
    
    # Check if there are tool calls
    if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
        logger.warning("⚠️ Tool node called but no tool_calls found")
        return {"messages": results}
    
    # Execute each tool call
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call.get("id", "unknown")
        
        logger.info(f"🛠️ Executing tool: {tool_name}")
        logger.debug(f"   Arguments: {tool_args}")
        
        selected_tool = tool_map.get(tool_name)
        
        if not selected_tool:
            error_msg = f"Tool '{tool_name}' not found in registry"
            logger.error(f"❌ {error_msg}")
            results.append(ToolMessage(
                tool_call_id=tool_id, 
                name=tool_name, 
                content=error_msg
            ))
            continue
        
        try:
            # Execute tool (async-safe)
            if hasattr(selected_tool, 'ainvoke'):
                output = await selected_tool.ainvoke(tool_args, config=config)
            else:
                output = selected_tool.invoke(tool_args, config=config)
            
            # ✅ GOOD: Safety limit to prevent memory issues
            output_str = str(output)
            if len(output_str) > 50000:
                output_str = output_str[:50000] + "\n\n[... Output truncated for length ...]"
                logger.warning(f"⚠️ Tool output truncated (was {len(str(output))} chars)")
            
            logger.info(f"✅ Tool '{tool_name}' succeeded ({len(output_str)} chars)")
            results.append(ToolMessage(
                tool_call_id=tool_id, 
                name=tool_name, 
                content=output_str
            ))
        
        except Exception as e:
            error_msg = f"Tool execution error: {type(e).__name__}: {str(e)}"
            logger.error(f"❌ Tool '{tool_name}' failed: {error_msg}")
            results.append(ToolMessage(
                tool_call_id=tool_id, 
                name=tool_name, 
                content=error_msg
            ))

    return {"messages": results}


def should_continue(state: ChatState) -> Literal["tools", "end"]:
    """Determine if we need to execute tools."""
    last_message = state["messages"][-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_names = [tc["name"] for tc in last_message.tool_calls]
        logger.info(f"🎯 Routing to tools: {tool_names}")
        return "tools"
    
    logger.info("🏁 Conversation turn complete")
    return "end"


# Build the graph
graph = StateGraph(ChatState)
graph.add_node("agent", chat_node)
graph.add_node("tools", dynamic_tool_node)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
graph.add_edge("tools", "agent")