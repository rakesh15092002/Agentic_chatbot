from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
from pathlib import Path
from app.services.rag_service import (
    process_and_store_pdf,
    delete_thread_documents
)
from app.services.thread_service import save_message

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCUMENTS_PATH = os.path.join(BASE_DIR, "../../documents")
Path(DOCUMENTS_PATH).mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    thread_id: str = Form(...)
):
    """
    Upload PDF documents and index them in Pinecone with thread_id.
    """
    try:
        if not thread_id or not thread_id.strip():
            raise HTTPException(status_code=400, detail="thread_id is required")
        
        results = []
        
        for file in files:
            # Check if file is PDF
            if not file.filename.lower().endswith('.pdf'):
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "message": "Only PDF files are supported"
                })
                continue
            
            # Process and store
            success, message = await process_and_store_pdf(file, thread_id)
            
            results.append({
                "filename": file.filename,
                "success": success,
                "message": message
            })
        
        # Check if any succeeded
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        # Save confirmation message to chat
        if len(successful) > 0:
            file_names = ", ".join([r["filename"] for r in successful])
            confirmation_message = (
                f"✅ **Document Uploaded Successfully**\n\n"
                f"📄 **Files:** {file_names}\n"
                f"📊 **Status:** {successful[0]['message']}\n\n"
                f"You can now ask me questions about {'this document' if len(successful) == 1 else 'these documents'}!"
            )
            save_message(thread_id, "assistant", confirmation_message)
        
        return JSONResponse(
            content={
                "success": len(successful) > 0,
                "message": f"Processed {len(successful)} files successfully, {len(failed)} failed",
                "results": results,
                "thread_id": thread_id,
                "total_processed": len(successful)
            },
            status_code=200 if len(successful) > 0 else 400
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/thread/{thread_id}")
async def delete_thread_docs(thread_id: str):
    """
    Delete all documents associated with a specific thread from Pinecone.
    """
    try:
        success, message = delete_thread_documents(thread_id)
        
        if success:
            return {"success": True, "message": message, "thread_id": thread_id}
        else:
            raise HTTPException(status_code=500, detail=message)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_documents():
    """List local temporary documents (if any)"""
    try:
        docs_path = Path(DOCUMENTS_PATH)
        if not docs_path.exists():
            return {"documents": [], "count": 0}
            
        files = [f.name for f in docs_path.iterdir() if f.is_file()]
        return {"documents": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))