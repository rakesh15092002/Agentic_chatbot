import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from pathlib import Path

load_dotenv()

# --- Configuration ---
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "chatbot")

class DocumentSearchInput(BaseModel):
    query: str = Field(description="Search query to find relevant information in uploaded documents")
    thread_id: str = Field(description="Thread ID to search documents for this specific conversation")

class RAGManager:
    def __init__(self):
        # 1. Google Embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        # 2. Pinecone client
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(INDEX_NAME)

    def search(self, query: str, thread_id: str, k: int = 3):
        """
        Search Pinecone for relevant documents filtered by thread_id.
        """
        try:
            # 1. Embed the query
            query_vector = self.embeddings.embed_query(query)
            
            # 2. Query Pinecone with thread_id filter
            results = self.index.query(
                vector=query_vector,
                top_k=k,
                include_metadata=True,
                filter={"thread_id": thread_id}
            )
            
            # 3. Extract context
            contexts = []
            for match in results.get('matches', []):
                if match.get('metadata') and match['metadata'].get('text'):
                    contexts.append({
                        'text': match['metadata']['text'],
                        'source': match['metadata'].get('source', 'Unknown'),
                        'score': match.get('score', 0),
                        'page': match['metadata'].get('page', 0)
                    })
            
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

rag_manager = RAGManager()

@tool("search_documents", args_schema=DocumentSearchInput)
def search_documents(query: str, thread_id: str) -> str:
    """
    Search through uploaded PDF documents (Knowledge Base) to find answers.
    
    Use this tool ONLY when:
    - User explicitly asks about "the PDF", "the file", or "the document"
    - User asks to "summarize the PDF" or similar
    - Question is clearly about uploaded document content
    
    DO NOT use this for:
    - General knowledge questions
    - Current events or news
    - Questions about well-known facts
    
    Returns: Relevant excerpts from uploaded documents with source information.
    """
    return rag_manager.search(query, thread_id)