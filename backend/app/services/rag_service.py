import os
import shutil
import logging
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)

# 1. Initialize Pinecone & Gemini
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

async def process_and_store_pdf(file: UploadFile, thread_id: str):
    """Process PDF and store in Pinecone with thread_id."""
    temp_filename = f"temp_{file.filename}"
    try:
        # Save temp file
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"📂 Processing {file.filename}...")

        # Load & Split
        loader = PyPDFLoader(temp_filename)
        documents = loader.load()
        chunks = text_splitter.split_documents(documents)

        vectors = []
        for i, doc in enumerate(chunks):
            # Embed
            vector_values = embeddings.embed_query(doc.page_content)
            
            # Metadata is CRITICAL for filtering
            metadata = {
                "text": doc.page_content,
                "source": file.filename,
                "thread_id": thread_id, # <--- This enables the filter
                "page": doc.metadata.get("page", 0)
            }
            
            vectors.append({
                "id": f"{thread_id}_{i}",
                "values": vector_values,
                "metadata": metadata
            })

        # Upsert in batches
        if vectors:
            index.upsert(vectors=vectors)
            logger.info(f"✅ Upserted {len(vectors)} chunks for thread {thread_id}")

        return True, f"Indexed {len(vectors)} chunks."

    except Exception as e:
        logger.error(f"❌ PDF Error: {e}")
        return False, str(e)
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

def search_documents(query: str, thread_id: str, top_k: int = 5):
    """Search Pinecone with Thread ID filter."""
    try:
        logger.info(f"🔍 Searching Pinecone: '{query}' (Thread: {thread_id})")
        
        query_vector = embeddings.embed_query(query)
        
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter={"thread_id": thread_id} # <--- MUST MATCH metadata above
        )
        
        matches = []
        for match in results.get('matches', []):
            if match.get('metadata'):
                matches.append({
                    'text': match['metadata'].get('text', ''),
                    'page': match['metadata'].get('page', 0),
                    'score': match.get('score', 0)
                })
        
        logger.info(f"✅ Found {len(matches)} matches")
        return matches

    except Exception as e:
        logger.error(f"❌ Search Error: {e}")
        return []

def delete_thread_documents(thread_id: str):
    """Clean up documents for a thread."""
    try:
        # Vector size must match your model (768 for Gemini 004)
        dummy = [0.0] * 768 
        results = index.query(
            vector=dummy, 
            top_k=1000, 
            filter={"thread_id": thread_id}
        )
        ids = [m['id'] for m in results.get('matches', [])]
        if ids:
            index.delete(ids=ids)
            return True, f"Deleted {len(ids)} chunks"
        return True, "No docs found"
    except Exception as e:
        return False, str(e)