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

# Llama 3.3 70B
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
)

UNIVERSAL_SYSTEM_PROMPT = """You are a highly capable AI assistant with access to real-time information and tools, including GitHub integration.

YOUR CAPABILITIES:
1. **search_documents**: Search user's uploaded PDF files.
2. **duckduckgo_search**: Get current information from the web.
3. **calculator**: Perform calculations.
4. **GitHub Tools**: When enabled, you have access to GitHub tools for searching repositories, reading files, and inspecting code.

DECISION RULES:

### 🚫 ANSWER DIRECTLY (No tools needed):
- **Static General Knowledge**: "What is the capital of France?", "What is a variable?"
- **Historical Facts**: "When was Python created?"
- **Chit-chat**: Greetings, casual conversation.

### ✅ USE TOOLS (MANDATORY for these cases):

**GitHub Tools** - Use when GitHub feature is enabled and:
- User asks to "find a library", "search repo", or "look for code" (Use available search tool).
- User asks to "read the code", "show me package.json", "check the README" of a specific repo (Use file reading tool).
- User wants to explore GitHub repositories or view code files.
- NOTE: Only use GitHub tools that are actually available to you. Check tool names carefully.

**duckduckgo_search** - Use when:
- **Current Public Figures/Roles**: "Who is the CEO of Google?"
- **Recent Events**: "Latest AI news", "Stock market crash today".
- **Dynamic Facts**: Info that changes over time.

**search_documents** - Use when:
- User mentions "the PDF", "the file", "uploaded document".
- User asks "summarize this" (referring to uploaded context).

**calculator** - Use when:
- User asks for mathematical calculations.

CRITICAL GUIDELINES:
- **Tool Names**: Use EXACT tool names provided to you. Do not guess or make up tool names.
- **GitHub**: When searching GitHub, provide the Repo Name, Description, and Star count when available. If the user wants to see code, you MUST fetch the file content using the appropriate tool.
- **Accuracy**: Do not rely on your internal training data for live code or recent news. Use the tools.
- **Citations**: Always mention where you got the info from (e.g., "According to the README file...").
- **Errors**: If a tool fails, inform the user clearly and suggest alternatives.
"""

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState, config):
    """Main chat node that binds tools dynamically per request."""
    messages = state["messages"]
    
    # Get MCP tools passed from config, or empty list if none
    dynamic_tools = config.get("configurable", {}).get("mcp_tools", [])
    
    # Combine Static Tools + MCP Tools
    all_tools = static_tools + dynamic_tools
    
    # Log available tools
    tool_names = [t.name for t in all_tools]
    logger.info(f"Available tools for this request: {tool_names}")
    
    # Bind the combined list to the LLM
    llm_with_tools = llm.bind_tools(all_tools)
    
    # --- STEP 1: SYSTEM PROMPT MANAGEMENT ---
    # Add available tool names to system prompt
    tools_info = ""
    if dynamic_tools:
        github_tool_names = [t.name for t in dynamic_tools]
        tools_info = f"\n\nAVAILABLE GITHUB TOOLS: {', '.join(github_tool_names)}"
        
    sys_msg_content = UNIVERSAL_SYSTEM_PROMPT + tools_info
    sys_msg = SystemMessage(content=sys_msg_content)

    # Ensure System Message is always at index 0 (Update or Insert)
    if messages and isinstance(messages[0], SystemMessage):
        messages[0] = sys_msg 
    else:
        messages = [sys_msg] + messages 

    # --- STEP 2: TOKEN-BASED TRIMMING (Updated Logic) ---
    try:
        # Separate System Prompt (Always Keep) vs History (Trimable)
        system_part = messages[:1]
        conversation_part = messages[1:]
        
        # Trim History based on TOKENS
        # Set to 5000 to accommodate GitHub code files + Chat context
        trimmed_conversation = trim_messages(
            conversation_part,
            max_tokens=5000,       # <-- Limit set to 5000 tokens
            strategy="last",       # Keep most recent messages
            token_counter=llm,     # Uses Llama 3 tokenizer for accuracy
            include_system=False,  # Don't count/trim system prompt here
            allow_partial=False,   # Don't cut a message in half
            start_on="human"       # Ensures chat always restarts with a user query
        )
        
        # Rejoin: System Prompt + Trimmed History
        messages = system_part + trimmed_conversation
        
    except Exception as e:
        logger.error(f"Error trimming messages: {e}")
        # Fallback to old method ONLY if trimming crashes
        if len(messages) > 31:
            messages = [messages[0]] + messages[-30:]

    # --- STEP 3: INVOKE LLM ---
    try:
        response = llm_with_tools.invoke(messages)
        logger.info(f"LLM Response type: {type(response)}")
        if hasattr(response, "tool_calls"):
            logger.info(f"Tool calls requested: {[tc['name'] for tc in response.tool_calls]}")
        return {"messages": [response]}
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in chat_node: {error_msg}", exc_info=True)
        
        # If it's a Groq tool parsing error, try without tools
        if "Failed to call a function" in error_msg or "tool" in error_msg.lower():
            logger.warning("⚠️ Groq tool error detected, retrying without tool binding...")
            try:
                # Retry without tools
                response_no_tools = llm.invoke(messages)
                return {"messages": [response_no_tools]}
            except Exception as retry_error:
                logger.error(f"Retry also failed: {retry_error}")
        
        return {"messages": [AIMessage(content=f"I encountered a technical error. Please try rephrasing your question or disabling the GitHub feature.")]}

async def dynamic_tool_node(state: ChatState, config):
    """Executes both Static and MCP tools."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Fetch all available tools again
    dynamic_tools = config.get("configurable", {}).get("mcp_tools", [])
    all_tools = static_tools + dynamic_tools
    
    # Create a map for quick lookup: {"tool_name": tool_function}
    tool_map = {tool.name: tool for tool in all_tools}
    
    results = []
    
    # Loop through tool calls requested by LLM
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call.get("id", "unknown")
            
            logger.info(f"🔧 Attempting to execute: {tool_name} with args: {tool_args}")
            
            selected_tool = tool_map.get(tool_name)
            
            if selected_tool:
                try:
                    logger.info(f"🛠️ Executing tool: {tool_name}")
                    
                    # Execute tool using ainvoke for async compatibility
                    output = await selected_tool.ainvoke(tool_args)
                    
                    logger.info(f"✅ Tool {tool_name} succeeded")
                    
                    results.append(
                        ToolMessage(
                            tool_call_id=tool_id,
                            name=tool_name,
                            content=str(output)
                        )
                    )
                except Exception as e:
                    error_msg = f"Error executing {tool_name}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    results.append(
                        ToolMessage(
                            tool_call_id=tool_id,
                            name=tool_name,
                            content=error_msg
                        )
                    )
            else:
                logger.error(f"❌ Tool '{tool_name}' not found in tool_map. Available: {list(tool_map.keys())}")
                results.append(
                    ToolMessage(
                        tool_call_id=tool_id,
                        name=tool_name,
                        content=f"Tool '{tool_name}' not found. Available tools: {', '.join(tool_map.keys())}"
                    )
                )
            
    return {"messages": results}

def should_continue(state: ChatState) -> Literal["tools", "end"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info(f"Routing to tools: {[tc['name'] for tc in last_message.tool_calls]}")
        return "tools"
    logger.info("Routing to end")
    return "end"

# Build Graph
graph = StateGraph(ChatState)

graph.add_node("agent", chat_node)
graph.add_node("tools", dynamic_tool_node)

graph.add_edge(START, "agent")
graph.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)
graph.add_edge("tools", "agent")