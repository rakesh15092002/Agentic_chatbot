import logging
import re
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
import yfinance as yf

logger = logging.getLogger(__name__)

# ==========================================
# 1. DUCKDUCKGO SEARCH (General Info)
# ==========================================
class SearchInput(BaseModel):
    query: str = Field(description="The exact search query. Be specific.")

@tool("duckduckgo_search", args_schema=SearchInput)
def duckduckgo_search(query: str) -> str:
    """
    Use this tool to find CURRENT information, news, or facts.
    Returns a summary of search results.
    """
    try:
        logger.info(f"🔍 Searching: {query}")
        wrapper = DuckDuckGoSearchAPIWrapper(max_results=3)
        results = wrapper.run(query)
        
        if not results or "No results" in results:
            return "No search results found. Please try a different query."
        
        return results[:1000] # Limit to avoid overwhelming the AI
    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"Search failed: {str(e)}"

# ==========================================
# 2. CALCULATOR (Safe Math)
# ==========================================
class CalculatorInput(BaseModel):
    expression: str = Field(description="A mathematical expression (e.g., '200 * 5 + 10').")

@tool("calculator", args_schema=CalculatorInput)
def calculator(expression: str) -> str:
    """
    Use this tool for ANY math calculation.
    """
    try:
        # 1. Clean up the input
        expression = expression.strip().replace("^", "**") # Fix common power symbol issue
        
        # 2. Security Check (Whitelist)
        allowed_chars = set("0123456789+-*/().% ")
        if not all(c in allowed_chars for c in expression):
            return f"Error: Expression contains invalid characters. Only numbers and math symbols allowed. You sent: {expression}"

        # 3. Calculate
        logger.info(f"🔢 Calculating: {expression}")
        # eval is safe here because we checked allowed_chars
        result = eval(expression, {"__builtins__": None}, {})
        
        return f"{expression} = {result}"
        
    except SyntaxError:
        return f"Error: Invalid syntax in expression '{expression}'"
    except ZeroDivisionError:
        return "Error: Cannot divide by zero"
    except Exception as e:
        return f"Calculation error: {str(e)}"

# ==========================================
# 3. STOCK PRICE (Real-time)
# ==========================================
class StockInput(BaseModel):
    symbol: str = Field(description="The stock ticker symbol (e.g., AAPL, NVDA, TSLA).")

@tool("get_stock_price", args_schema=StockInput)
def get_stock_price(symbol: str) -> str:
    """
    Get the current real-time stock price.
    """
    symbol = symbol.upper().strip()
    try:
        logger.info(f"📈 Stock Check: {symbol}")
        ticker = yf.Ticker(symbol)
        
        # Method A: Fast Info (Real-time)
        price = ticker.fast_info.get('last_price')
        
        # Method B: History (Fallback)
        if not price:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]

        if price:
            return f"The current price of {symbol} is ${price:.2f}"
        
        return f"Error: Could not find stock price for symbol '{symbol}'. Is it correct?"
        
    except Exception as e:
        return f"Error fetching stock data: {str(e)}"

# ==========================================
# 4. WEATHER (Search-Based)
# ==========================================
class WeatherInput(BaseModel):
    city: str = Field(description="The name of the city (e.g., 'New York', 'Mumbai').")

@tool("get_weather", args_schema=WeatherInput)
def get_weather(city: str) -> str:
    """
    Finds the current weather for a city. 
    Note: This searches the web for the latest report.
    """
    try:
        logger.info(f"🌤️ Weather Check: {city}")
        wrapper = DuckDuckGoSearchAPIWrapper(max_results=1)
        
        # Specific query to get a good snippet
        query = f"current weather temperature in {city} celsius fahrenheit"
        result = wrapper.run(query)
        
        if not result:
            return f"Could not find weather info for {city}."
            
        # We explicitly tell the AI this is a search result
        return f"SEARCH RESULT for '{city} Weather':\n{result}\n\n(Please summarize this weather data for the user)."
        
    except Exception as e:
        return f"Weather search failed: {str(e)}"

# ==========================================
# 5. DOCUMENT SEARCH (RAG - Summary Optimized)
# ==========================================
class DocumentSearchInput(BaseModel):
    query: str = Field(description="The specific keywords to search for. For summaries, use 'Experience Skills Education Overview'.")

@tool("search_documents", args_schema=DocumentSearchInput)
def search_documents(query: str, config: RunnableConfig) -> str:
    """
    Search inside the uploaded PDF documents.
    IMPORTANT: If the user asks to 'Summarize', search for 'key points overview features' instead of the word 'summarize'.
    """
    try:
        # 1. Get Thread ID
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return "Error: Cannot search documents (No Thread ID found in config)."

        # 2. Import RAG Service (Lazy import to avoid circular dependency)
        from app.services.rag_service import search_documents as rag_search
        
        logger.info(f"📄 RAG Search Query: '{query}' for Thread: {thread_id}")
        
        # 3. Perform Search (Increased top_k for better context)
        contexts = rag_search(query, thread_id, top_k=5)
        
        if not contexts:
            logger.warning(f"⚠️ No matches found for '{query}'")
            return (
                "No specific matches found in the document. "
                "If the user asked for a summary, try asking specific questions like 'What is the experience?' or 'What are the skills?'."
            )
            
        # 4. Format Results
        formatted_results = "\n\n".join(
            [f"[Source: Page {c['page']}]\n{c['text']}" for c in contexts]
        )
        return f"FOUND DOCUMENTS:\n{formatted_results}"
        
    except Exception as e:
        logger.error(f"RAG Error: {e}", exc_info=True)
        return f"Error searching documents: {str(e)}"

# ==========================================
# EXPORT ALL TOOLS
# ==========================================
tools = [
    duckduckgo_search,
    calculator,
    get_stock_price,
    get_weather,
    search_documents
]

logger.info(f"📦 Loaded {len(tools)} tools: {[t.name for t in tools]}")