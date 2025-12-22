"""API endpoint for PDF upload and LiveKit token generation."""

import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from livekit import api
from rag.pdf_processor import process_pdf_for_rag
from rag.retriever import create_vector_store, add_documents_to_vector_store

app = FastAPI(title="Paradise API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Check if Pinecone is configured
    if not os.getenv("PINECONE_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="Pinecone is not configured. Please set PINECONE_API_KEY."
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Process PDF
        chunks = process_pdf_for_rag(tmp_file_path)
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the PDF"
            )
        
        # Get index name
        index_name = os.getenv("PINECONE_INDEX_NAME", "paradise-travel-index")
        
        # Create vector store
        vector_store = create_vector_store(index_name)
        
        # Add documents to vector store
        metadatas = [
            {"source": file.filename, "chunk_index": i}
            for i in range(len(chunks))
        ]
        add_documents_to_vector_store(vector_store, chunks, metadatas)
        
        return {
            "success": True,
            "message": f"Successfully processed and indexed {len(chunks)} chunks from {file.filename}",
            "chunks": len(chunks),
            "filename": file.filename,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


class TokenRequest(BaseModel):
    """Request model for token generation."""
    identity: str = "user"
    name: str = "User"
    room: str = "paradise-room"


@app.post("/api/token")
async def generate_token(request: TokenRequest):
    """Generate a LiveKit access token for the frontend."""
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not all([livekit_url, api_key, api_secret]):
        raise HTTPException(
            status_code=500,
            detail="LiveKit credentials not configured. Please set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET."
        )
    
    try:
        # Create access token
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

