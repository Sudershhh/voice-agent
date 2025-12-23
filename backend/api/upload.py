"""API endpoint for PDF upload and LiveKit token generation."""

import os
import tempfile
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from livekit import api
from rag.pdf_processor import process_pdf_for_rag
from rag.retriever import (
    create_vector_store,
    add_documents_to_vector_store,
    get_namespace_for_destination,
)
from rag.storage_monitor import can_upload, check_storage_quota, get_storage_usage
from rag.retriever import initialize_pinecone
from rag.document_classifier import classify_document_type, extract_destination_from_filename
from config import config

app = FastAPI(title="Paradise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF file with enhanced validation and metadata extraction.
    """
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    if not config.PINECONE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Pinecone is not configured. Please set PINECONE_API_KEY."
        )
    
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    MAX_FILE_SIZE_MB = 10.0
    WARNING_FILE_SIZE_MB = 5.0
    
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB} MB)"
        )
    
    if file_size_mb > WARNING_FILE_SIZE_MB:
        pass
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        index_name = config.PINECONE_INDEX_NAME
        
        document_type = classify_document_type(file.filename)
        destination = extract_destination_from_filename(file.filename)
        
        estimated_chunks = int(file_size_mb * 75)
        
        upload_check = can_upload(index_name, estimated_chunks)
        if not upload_check.get("can_upload", True):
            raise HTTPException(
                status_code=507,
                detail=f"Cannot upload: {upload_check.get('reason', 'Storage quota exceeded')}"
            )
        
        if upload_check.get("warning", False):
            pass
        
        chunks, metadatas = process_pdf_for_rag(
            tmp_file_path,
            filename=file.filename,
            document_type=document_type,
            destination=destination,
        )
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the PDF"
            )
        
        namespace = get_namespace_for_destination(destination) if destination else None
        
        vector_store = create_vector_store(index_name, namespace=namespace)
        
        add_documents_to_vector_store(
            vector_store,
            chunks,
            metadatas,
            namespace=namespace,
        )
        
        quota_status = check_storage_quota(index_name)
        
        return {
            "success": True,
            "message": f"Successfully processed and indexed {len(chunks)} chunks from {file.filename}",
            "chunks": len(chunks),
            "filename": file.filename,
            "document_type": document_type,
            "destination": destination,
            "namespace": namespace,
            "file_size_mb": round(file_size_mb, 2),
            "storage_status": {
                "estimated_storage_gb": quota_status.get("estimated_storage_gb", 0),
                "usage_percent": quota_status.get("usage_percent", 0),
                "warning": quota_status.get("warning", False),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )
    finally:
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/storage-status")
async def get_storage_status():
    """Get current storage usage status."""
    if not config.PINECONE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Pinecone is not configured. Please set PINECONE_API_KEY."
        )
    
    index_name = config.PINECONE_INDEX_NAME
    quota_status = check_storage_quota(index_name)
    
    if "error" in quota_status:
        raise HTTPException(
            status_code=500,
            detail=quota_status["error"]
        )
    
    return quota_status


@app.get("/api/indexes")
async def list_indexes():
    """List all Pinecone indexes."""
    if not config.PINECONE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Pinecone is not configured. Please set PINECONE_API_KEY."
        )
    
    try:
        pc = initialize_pinecone()
        existing_indexes = pc.list_indexes()
        
        indexes = []
        if hasattr(existing_indexes, 'indexes'):
            for idx in existing_indexes.indexes:
                indexes.append({
                    "name": idx.name,
                    "dimension": idx.dimension,
                    "metric": idx.metric,
                    "status": idx.status.state if hasattr(idx.status, 'state') else "unknown",
                    "ready": idx.status.ready if hasattr(idx.status, 'ready') else False,
                })
        else:
            index_names = existing_indexes.names() if hasattr(existing_indexes, 'names') else []
            for name in index_names:
                try:
                    index = pc.Index(name)
                    stats = index.describe_index_stats()
                    indexes.append({
                        "name": name,
                        "dimension": stats.get("dimension", 1536),
                        "metric": "cosine",
                        "status": "Ready",
                        "ready": True,
                    })
                except Exception as e:
                    indexes.append({
                        "name": name,
                        "dimension": None,
                        "metric": None,
                        "status": "Error",
                        "ready": False,
                        "error": str(e),
                    })
        
        return {
            "indexes": indexes,
            "count": len(indexes),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing indexes: {str(e)}"
        )


@app.get("/api/indexes/{index_name}/namespaces")
async def list_namespaces(index_name: str):
    """List all namespaces in a Pinecone index with record counts."""
    if not config.PINECONE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Pinecone is not configured. Please set PINECONE_API_KEY."
        )
    
    try:
        pc = initialize_pinecone()
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        
        namespaces_info = []
        namespaces = stats.get("namespaces", {})
        
        for namespace_name, namespace_stats in namespaces.items():
            namespaces_info.append({
                "name": namespace_name if namespace_name else "default",
                "record_count": namespace_stats.get("vector_count", 0) if isinstance(namespace_stats, dict) else 0,
            })
        
        if not namespaces_info:
            total_count = stats.get("total_vector_count", 0)
            if total_count > 0:
                namespaces_info.append({
                    "name": "default",
                    "record_count": total_count,
                })
        
        return {
            "index_name": index_name,
            "namespaces": namespaces_info,
            "total_namespaces": len(namespaces_info),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing namespaces for index '{index_name}': {str(e)}"
        )


@app.get("/api/indexes/{index_name}/stats")
async def get_index_stats(index_name: str):
    """Get comprehensive statistics for a Pinecone index."""
    if not config.PINECONE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Pinecone is not configured. Please set PINECONE_API_KEY."
        )
    
    try:
        pc = initialize_pinecone()
        storage_info = get_storage_usage(pc, index_name)
        
        quota_status = check_storage_quota(index_name)
        
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        
        namespaces_info = {}
        namespaces = stats.get("namespaces", {})
        for namespace_name, namespace_stats in namespaces.items():
            ns_key = namespace_name if namespace_name else "default"
            namespaces_info[ns_key] = {
                "record_count": namespace_stats.get("vector_count", 0) if isinstance(namespace_stats, dict) else 0,
            }
        
        return {
            "index_name": index_name,
            "dimension": storage_info.get("dimension", stats.get("dimension", 1536)),
            "total_vectors": storage_info.get("total_vectors", stats.get("total_vector_count", 0)),
            "namespaces": namespaces_info,
            "total_namespaces": len(namespaces_info),
            "storage": {
                "estimated_storage_mb": storage_info.get("estimated_storage_mb", 0),
                "estimated_storage_gb": storage_info.get("estimated_storage_gb", 0),
                "index_fullness": storage_info.get("index_fullness", 0),
            },
            "quota": {
                "within_quota": quota_status.get("within_quota", True),
                "usage_percent": quota_status.get("usage_percent", 0),
                "limit_gb": quota_status.get("limit_gb", 2.0),
                "remaining_gb": quota_status.get("remaining_gb", 2.0),
                "warning": quota_status.get("warning", False),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats for index '{index_name}': {str(e)}"
        )


class TokenRequest(BaseModel):
    """Request model for token generation."""
    identity: str = "user"
    name: str = "User"
    room: str = "paradise-room"


@app.post("/api/token")
async def generate_token(request: TokenRequest):
    """Generate a LiveKit access token for the frontend."""
    livekit_url = config.LIVEKIT_URL
    api_key = config.LIVEKIT_API_KEY
    api_secret = config.LIVEKIT_API_SECRET
    
    if not all([livekit_url, api_key, api_secret]):
        raise HTTPException(
            status_code=500,
            detail="LiveKit credentials not configured. Please set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET."
        )
    
    try:
        token = api.AccessToken(api_key, api_secret) \
            .with_identity(request.identity) \
            .with_name(request.name) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=request.room,
                can_publish=True,
                can_subscribe=True,
            )) \
            .to_jwt()
        
        return {
            "token": token,
            "url": livekit_url,
            "room": request.room,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate token: {str(e)}"
        )

