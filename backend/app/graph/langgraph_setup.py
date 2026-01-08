import os
from typing import Annotated, TypedDict, Literal
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from app.utils.tools import tools
import logging

logger = logging.getLogger(__name__)
load_dotenv()

# Llama 3.3 70B
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
)

llm_with_tools = llm.bind_tools(tools)

# ✅ CHANGE: Optimized Prompt to distinguish "Static" vs "Dynamic" facts
# ✅ CHANGE: Optimized Prompt to fix "summarize this" issues
UNIVERSAL_SYSTEM_PROMPT = """You are a highly capable AI assistant with access to real-time information and tools.

YOUR CAPABILITIES:
1. **search_documents**: Search user's uploaded PDF files.
2. **duckduckgo_search**: Get current information from the web.
3. **calculator**: Perform calculations.
4. **get_stock_price**: Get stock prices.
5. **get_weather**: Get weather information.

DECISION RULES:

### 🚫 ANSWER DIRECTLY (No tools needed):
- **Static General Knowledge**: "What is the capital of France?", "What is photosynthesis?"
- **Historical Facts**: "Who was the first US president?", "When did WWII end?"
- **Coding Tasks**: Writing code, debugging, explaining syntax.
- **Chit-chat**: Greetings, casual conversation.

### ✅ USE TOOLS (MANDATORY for these cases):

**duckduckgo_search** - Use when:
- **Current Public Figures/Roles**: "Who is the *current* President of America?", "Who is the CEO of Twitter now?" (Even if you think you know, VERIFY it).
- **Recent Events**: "What is happening in the world?", "Latest news on AI".
- **Dynamic Facts**: "What is the population of India?", "Who won the match yesterday?".
- **Time-Sensitive Info**: Anything that might have changed since your training cutoff.

**search_documents** - Use when:
- User mentions "the PDF", "the file", "uploaded document".
- User asks vague questions like "summarize this", "explain this", or "what is this about" (assume they refer to the last uploaded file).
- You need context that isn't in the conversation history or general knowledge.

**Other tools**: Use as appropriate for calculations, stocks, weather.

CRITICAL GUIDELINES:
- If a user asks about a **current** official, leader, or status, you MUST use `duckduckgo_search` to ensure the answer is up-to-date.
- Do not rely on your internal training data for facts that change over time (prices, leaders, laws).
- Cite sources when using search results.
"""

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    """Main chat node that calls the LLM with tools."""
    messages = state["messages"]
    
    # Add system prompt if not present
    if not messages or not isinstance(messages[0], SystemMessage):
        sys_msg = SystemMessage(content=UNIVERSAL_SYSTEM_PROMPT)
        messages = [sys_msg] + messages
    
    # Keep only last 30 messages + system prompt
    if len(messages) > 31:
        messages = [messages[0]] + messages[-30:]
    
    try:
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    except Exception as e:
        logger.error(f"Error in chat_node: {str(e)}")
        error_msg = AIMessage(
            content="I apologize, but I encountered a technical issue. Please try asking your question in a different way."
        )
        return {"messages": [error_msg]}

def should_continue(state: ChatState) -> Literal["tools", "end"]:
    """Determine if we should call tools or end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If there are tool calls, route to tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    # Otherwise end
    return "end"

# Tool node handles tool execution
tool_node = ToolNode(tools)

# Build the graph
graph = StateGraph(ChatState)
graph.add_node("agent", chat_node)
graph.add_node("tools", tool_node)

# Add edges
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