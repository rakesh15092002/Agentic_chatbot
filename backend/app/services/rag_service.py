# backend/app/services/rag_service.py
import os
import shutil
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import logging

logger = logging.getLogger(__name__)

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

# ✅ Use Google Gemini Embeddings (No DLL issues!)
embeddings = GoogleGenerativeAIEmbeddings(
    model="text-embedding-004",  # 768 dimensions
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# Text splitter for chunking documents
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

async def process_and_store_pdf(file: UploadFile, thread_id: str):
    """
    1. Saves file temporarily.
    2. Extracts text & chunks it.
    3. Embeds & Upserts to Pinecone with thread_id metadata.
    """
    temp_filename = None
    
    try:
        # 1. Save file temporarily
        temp_filename = f"temp_{file.filename}"
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Processing PDF: {file.filename} for thread: {thread_id}")

        # 2. Load PDF
        loader = PyPDFLoader(temp_filename)
        documents = loader.load()
        
        # 3. Split into chunks
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks")

        # 4. Prepare Vectors with Metadata
        vectors_to_upsert = []
        
        for i, doc in enumerate(chunks):
            # Create Embedding
            vector_values = embeddings.embed_query(doc.page_content)
            
            # Create Unique ID for this chunk
            chunk_id = f"{thread_id}_{file.filename}_{i}"

            vectors_to_upsert.append({
                "id": chunk_id,
                "values": vector_values,
                "metadata": {
                    "text": doc.page_content,
                    "source": file.filename,
                    "thread_id": thread_id,
                    "chunk_index": i,
                    "page": doc.metadata.get("page", 0)
                }
            })

        # 5. Upsert to Pinecone in batches
        if vectors_to_upsert:
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                index.upsert(vectors=batch)
            
            logger.info(f"Uploaded {len(vectors_to_upsert)} vectors to Pinecone")

        # 6. Cleanup
        if temp_filename and os.path.exists(temp_filename):
            os.remove(temp_filename)
            
        return True, f"Successfully indexed {len(vectors_to_upsert)} chunks from {file.filename}"

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        # Cleanup on error
        if temp_filename and os.path.exists(temp_filename):
            os.remove(temp_filename)
        return False, str(e)


def search_documents(query: str, thread_id: str, top_k: int = 5):
    """
    Search Pinecone for relevant documents filtered by thread_id.
    """
    try:
        # 1. Embed the query
        query_vector = embeddings.embed_query(query)
        
        # 2. Query Pinecone with thread_id filter
        results = index.query(
            vector=query_vector,
            top_k=top_k,
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
        
        return contexts
    
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        return []


def delete_thread_documents(thread_id: str):
    """
    Delete all documents associated with a thread_id from Pinecone.
    """
    try:
        # Query to get all IDs for this thread
        dummy_vector = [0.0] * 768  # Gemini embedding-001 dimension
        results = index.query(
            vector=dummy_vector,
            top_k=10000,
            include_metadata=True,
            filter={"thread_id": thread_id}
        )
        
        # Extract IDs and delete
        ids_to_delete = [match['id'] for match in results.get('matches', [])]
        
        if ids_to_delete:
            index.delete(ids=ids_to_delete)
            logger.info(f"Deleted {len(ids_to_delete)} vectors for thread {thread_id}")
            return True, f"Deleted {len(ids_to_delete)} document chunks"
        else:
            return True, "No documents found for this thread"
    
    except Exception as e:
        logger.error(f"Error deleting thread documents: {str(e)}")
        return False, str(e)