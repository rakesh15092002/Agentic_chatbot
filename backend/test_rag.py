import os
from dotenv import load_dotenv
# .env load karna zaroori hai
load_dotenv()

from app.utils.rag_tools import rag_manager

# PDF se juda koi sawal puchiye (SQL Commands ke baare mein)
query = "Explain the SELECT command" 

print(f"🔎 Searching for: '{query}'...")

# Pinecone se search karega
answer = rag_manager.search(query)

print("\n--- 📄 RESULT FROM PINECONE ---")
print(answer)
print("-------------------------------")