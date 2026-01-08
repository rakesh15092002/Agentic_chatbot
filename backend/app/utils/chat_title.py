import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Fast model specifically for generating short titles
title_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),  # Your Groq API key from environment variables
    temperature=0.5,  # Controls randomness; 0.5 is balanced
)

async def generate_chat_title(first_message: str) -> str:
    """
    Generates a short 3-5 word title from the user's first message.
    """
    # Prompt to instruct the model to summarize
    prompt = f"""
    Summarize this message into a short, concise title (max 5 words).
    Message: "{first_message}"
    
    Rules:
    - Do not use quotes.
    - Do not add "Title:" prefix.
    - Only return the summary words.
    - Example: "Python List Help" or "Weather in London"
    """
    
    try:
        # Call the model asynchronously
        response = await title_llm.ainvoke([HumanMessage(content=prompt)])
        
        # Cleanup: remove any unwanted quotes or prefixes
        title = response.content.strip().replace('"', '').replace("Title:", "").strip()
        
        # Trim if the model accidentally returns a long sentence
        if len(title) > 50:
            title = title[:47] + "..."
            
        return title  # Return the final short title
        
    except Exception as e:
        print(f"Error generating title: {e}")
        return "New Chat"  # Fallback title if anything goes wrong
