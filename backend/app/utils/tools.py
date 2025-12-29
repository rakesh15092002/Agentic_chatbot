import requests
import yfinance as yf
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

# ==========================================
# 1. SEARCH TOOL
# ==========================================
class SearchInput(BaseModel):
    query: str = Field(
        description="Search query for finding current information, news, facts, or events."
    )

@tool("duckduckgo_search", args_schema=SearchInput)
def duckduckgo_search(query: str) -> str:
    """
    Search the web for current information, news, events, and facts.
    
    Use this ONLY for:
    - Current events and breaking news
    - Recent developments (last few days/weeks)
    - Time-sensitive information
    - Information you genuinely don't know
    
    DO NOT use for general knowledge like "Who is Prime Minister of India" - you already know this.
    
    Returns: Text with relevant search results
    """
    try:
        wrapper = DuckDuckGoSearchAPIWrapper(max_results=5)
        results = wrapper.run(query)
        
        if not results or results.strip() == "":
            return f"No search results found for '{query}'. Try rephrasing your search query."
        
        return results
    
    except Exception as e:
        return f"Search error: {str(e)}. Please try a different query."

# ==========================================
# 2. CALCULATOR
# ==========================================
class CalculatorInput(BaseModel):
    expression: str = Field(
        description="Mathematical expression to evaluate. Examples: '5 + 3', '100 * 2.5'"
    )

@tool("calculator", args_schema=CalculatorInput)
def calculator(expression: str) -> str:
    """
    Perform mathematical calculations.
    
    Supports: +, -, *, /, parentheses
    Examples: '25 * 4', '(100 + 50) / 2'
    
    Returns: The calculated result
    """
    try:
        allowed_chars = set("0123456789+-*/(). ")
        if not all(char in allowed_chars for char in expression):
            return "Error: Invalid characters. Only use numbers and operators (+, -, *, /, parentheses)."
        
        result = eval(expression)
        return f"{expression} = {result}"
    
    except ZeroDivisionError:
        return "Error: Division by zero."
    except Exception as e:
        return f"Calculation error: {str(e)}"

# ==========================================
# 3. STOCK PRICE TOOL
# ==========================================
class StockInput(BaseModel):
    symbol: str = Field(
        description="Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'TSLA')"
    )

@tool("get_stock_price", args_schema=StockInput)
def get_stock_price(symbol: str) -> str:
    """
    Get current stock price for a ticker symbol.
    
    Examples: AAPL (Apple), MSFT (Microsoft), GOOGL (Google)
    
    Returns: Current stock price and currency
    """
    try:
        ticker = yf.Ticker(symbol.upper())
        price = ticker.fast_info.get('last_price')
        
        if price is None:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
        
        if price:
            currency = ticker.fast_info.get('currency', 'USD')
            return f"{symbol.upper()} is currently trading at {round(price, 2)} {currency}"
        else:
            return f"Could not retrieve price for {symbol.upper()}. Verify the ticker symbol."
    
    except Exception as e:
        return f"Error fetching stock price: {str(e)}"

# ==========================================
# 4. WEATHER TOOL
# ==========================================
class WeatherInput(BaseModel):
    city: str = Field(
        description="City name (e.g., 'London', 'New York', 'Tokyo')"
    )

@tool("get_weather", args_schema=WeatherInput)
def get_weather(city: str) -> str:
    """
    Get current weather for a city.
    
    Returns: Temperature, condition, and humidity
    """
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            
            temp_c = current['temp_C']
            temp_f = current['temp_F']
            condition = current['weatherDesc'][0]['value']
            humidity = current['humidity']
            
            return f"Weather in {city.title()}: {temp_c}°C ({temp_f}°F), {condition}, Humidity: {humidity}%"
        else:
            return f"Could not find weather for '{city}'."
    
    except Exception as e:
        return f"Weather error: {str(e)}"

# ==========================================
# 5. DOCUMENT SEARCH TOOL (with config for thread_id)
# ==========================================
class DocumentSearchInput(BaseModel):
    query: str = Field(
        description="Search query to find information in uploaded PDF documents"
    )

@tool("search_documents", args_schema=DocumentSearchInput)
def search_documents(query: str, config: RunnableConfig) -> str:
    """
    Search through uploaded PDF documents (Knowledge Base).
    
    Use this tool ONLY when:
    - User asks about "the PDF", "the document", "the file I uploaded"
    - User says "summarize the PDF" or similar
    - Question is clearly about uploaded document content
    
    DO NOT use for general knowledge questions.
    
    Returns: Relevant excerpts from documents with sources.
    """
    try:
        # Extract thread_id from config
        thread_id = config.get("configurable", {}).get("thread_id", "")
        
        if not thread_id:
            return "Error: No thread ID found. Cannot search documents."
        
        # Import here to avoid circular imports
        from app.services.rag_service import search_documents as rag_search
        
        # Call the RAG search with thread_id
        contexts = rag_search(query, thread_id, top_k=3)
        
        if not contexts:
            return "No relevant information found in your uploaded documents."
        
        # Format the results
        formatted_results = []
        for ctx in contexts:
            formatted_results.append(
                f"[Source: {ctx['source']}, Page: {ctx['page']}, Relevance: {ctx['score']:.2f}]\n"
                f"{ctx['text']}"
            )
        
        return "\n\n---\n\n".join(formatted_results)
    
    except Exception as e:
        return f"Error searching documents: {str(e)}"

# ==========================================
# EXPORT ALL TOOLS
# ==========================================
tools = [duckduckgo_search, calculator, get_stock_price, get_weather, search_documents]