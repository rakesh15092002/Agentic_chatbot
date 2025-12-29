import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv

# LangGraph & LangChain Imports
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Import your tools
from app.utils.tools import tools

load_dotenv()

# ==========================================
# 1. LLM SETUP
# ==========================================
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
)

llm_with_tools = llm.bind_tools(tools)

# ==========================================
# 2. UPDATED SYSTEM PROMPT
# ==========================================
UNIVERSAL_SYSTEM_PROMPT = """You are a highly capable AI assistant with access to real-time information, personal documents, and tools.

YOUR CORE CAPABILITIES:
1. **Knowledge Base (search_documents)**: Access and retrieve information from the user's uploaded PDF files and documents.
2. **Search (duckduckgo_search)**: Get current information, news, facts about people, places, events.
3. **Calculator**: Perform mathematical calculations.
4. **Stock Prices (get_stock_price)**: Get real-time stock market data.
5. **Weather (get_weather)**: Get current weather information.

DECISION MAKING RULES - FOLLOW THESE STRICTLY:

### 🚫 WHEN TO ANSWER DIRECTLY (DO NOT USE TOOLS):
- **Coding & Technical Tasks**: Writing code, debugging, explaining syntax.
- **General Knowledge**: Static facts, history, science, definitions (e.g., "Who is Newton?", "What is photosynthesis?").
- **Well-Known Facts**: "Who is the Prime Minister of India?" - you know this is Narendra Modi.
- **Chit-Chat**: Greetings, "How are you?", questions about your identity.
- **Logic/Reasoning**: Common sense questions.

### ✅ WHEN TO USE TOOLS:

**1. Knowledge Base (search_documents):**
- ONLY when user explicitly asks about "the PDF", "the document", "the file I uploaded"
- Questions like "summarize the PDF", "what does the document say about X"
- If uncertain whether to search documents, DON'T - answer directly instead

**2. Search (duckduckgo_search):**
- Real-time information: "What happened today?", "current news about X"
- Recent events: "Who won yesterday's game?"
- Stock market trends, breaking news
- When you genuinely don't know and it's time-sensitive

**3. Calculator:**
- Mathematical calculations with specific numbers

**4. Stock Price:**
- Current stock prices for specific ticker symbols

**5. Weather:**
- Current weather or forecasts for specific locations

CRITICAL GUIDELINES:
- For general knowledge (Prime Minister, historical facts, definitions), answer DIRECTLY without tools
- Use search_documents ONLY when explicitly asked about uploaded files
- Use duckduckgo_search ONLY for current/recent events
- When answering directly, be confident and don't mention not having access to information you clearly have
- NEVER say "I don't have access to real-time information" for general knowledge questions"""

# ==========================================
# 3. STATE (Simple - no thread_id needed here)
# ==========================================
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    """Enhanced agent node with better context management."""
    messages = state["messages"]
    
    # Add system message only if not present
    if not messages or not isinstance(messages[0], SystemMessage):
        sys_msg = SystemMessage(content=UNIVERSAL_SYSTEM_PROMPT)
        messages = [sys_msg] + messages
    
    # Smart context window management
    if len(messages) > 31:
        messages = [messages[0]] + messages[-30:]
    
    # Invoke LLM
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Use built-in ToolNode - much simpler!
tool_node = ToolNode(tools)

# ==========================================
# 4. BUILD GRAPH
# ==========================================
graph = StateGraph(ChatState)

# Add Nodes
graph.add_node("agent", chat_node)
graph.add_node("tools", tool_node)

# Add Edges
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", tools_condition)
graph.add_edge("tools", "agent")