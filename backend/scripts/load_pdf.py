"""Script to load a PDF into Pinecone for RAG."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.pdf_processor import process_pdf_for_rag
from rag.retriever import (
    create_vector_store,
    add_documents_to_vector_store,
    get_namespace_for_destination,
)
from config import config


def main():
    """Load PDF into Pinecone with enhanced metadata."""
    pdf_path = config.PDF_PATH
    index_name = config.PINECONE_INDEX_NAME
    
    if not os.path.exists(pdf_path):
        return
    
    chunks, metadatas = process_pdf_for_rag(pdf_path)
    
    if not chunks:
        return
    
    destination = None
    if metadatas and len(metadatas) > 0:
        destination = metadatas[0].get("destination")
    
    namespace = get_namespace_for_destination(destination) if destination else None
    
    if namespace:
        pass
    
    vector_store = create_vector_store(index_name, namespace=namespace)
    
    add_documents_to_vector_store(vector_store, chunks, metadatas, namespace=namespace)
    
    if destination:
        pass
    if metadatas:
        doc_type = metadatas[0].get("document_type", "unknown")


if __name__ == "__main__":
    main()

