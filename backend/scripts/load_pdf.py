"""Script to load a PDF into Pinecone for RAG."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.pdf_processor import process_pdf_for_rag
from rag.retriever import create_vector_store, add_documents_to_vector_store


def main():
    """Load PDF into Pinecone."""
    load_dotenv()
    
    pdf_path = os.getenv("PDF_PATH", "data/sample_travel_guide.pdf")
    index_name = os.getenv("PINECONE_INDEX_NAME", "paradise-travel-index")
    
    if not os.path.exists(pdf_path):
        return
    
    chunks = process_pdf_for_rag(pdf_path)
    
    if not chunks:
        return
    
    vector_store = create_vector_store(index_name)
    
    metadatas = [{"source": pdf_path, "chunk_index": i} for i in range(len(chunks))]
    add_documents_to_vector_store(vector_store, chunks, metadatas)


if __name__ == "__main__":
    main()

