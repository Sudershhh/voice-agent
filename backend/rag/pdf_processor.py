"""PDF processing for RAG pipeline."""

import os
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from rag.document_classifier import (
    classify_document_type,
    extract_destination_from_filename,
    extract_destination_from_content,
    create_document_metadata,
    create_chunk_metadata,
    extract_section_from_content,
)


def load_pdf(file_path: str) -> Tuple[str, Dict[str, any]]:
    """
    Load and extract text from a PDF file with metadata.
    
    Returns:
        Tuple of (text, pdf_metadata)
    """
    reader = PdfReader(file_path)
    text = ""
    pages = []
    
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        text += page_text + "\n"
        pages.append({
            "page_number": i + 1,
            "text": page_text,
        })
    
    # Extract PDF metadata
    pdf_metadata = {}
    if reader.metadata:
        pdf_metadata = {
            "title": reader.metadata.get("/Title", ""),
            "author": reader.metadata.get("/Author", ""),
            "subject": reader.metadata.get("/Subject", ""),
        }
    
    return text, {
        "total_pages": len(pages),
        "pages": pages,
        "pdf_metadata": pdf_metadata,
    }


def detect_sections(text: str) -> List[Tuple[int, str, str]]:
    """
    Detect section headings in text.
    
    Returns:
        List of (position, heading_text, section_type) tuples
    """
    sections = []
    lines = text.split("\n")
    
    # Patterns for section headings
    heading_patterns = [
        (r"^#+\s+(.+)$", "markdown"),  # Markdown headers
        (r"^[A-Z][A-Z\s]{10,}$", "all_caps"),  # ALL CAPS headings
        (r"^\d+\.\s+([A-Z][^\.]+)$", "numbered"),  # Numbered sections
        (r"^Chapter\s+\d+[:\s]+(.+)$", "chapter"),  # Chapter headings
    ]
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if len(line_stripped) < 5:  # Skip very short lines
            continue
            
        for pattern, pattern_type in heading_patterns:
            match = re.match(pattern, line_stripped)
            if match:
                heading = match.group(1) if match.groups() else line_stripped
                section_type = extract_section_from_content(heading)
                sections.append((i, heading, section_type))
                break
    
    return sections


def chunk_text_with_sections(
    text: str,
    chunk_size: int = 1500,
    chunk_overlap: int = 300,
    document_type: str = "travel_guide"
) -> List[Tuple[str, Dict[str, any]]]:
    """
    Split text into chunks with section awareness.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between chunks
        document_type: Type of document (affects chunk size)
    
    Returns:
        List of (chunk_text, chunk_metadata) tuples
    """
    # Adjust chunk size based on document type
    type_chunk_sizes = {
        "travel_guide": (1500, 300),
        "destination_info": (1500, 300),
        "restaurant_guide": (800, 150),
        "hotel_guide": (800, 150),
        "transport_guide": (1000, 200),
    }
    
    if document_type in type_chunk_sizes:
        chunk_size, chunk_overlap = type_chunk_sizes[document_type]
    
    # Detect sections
    sections = detect_sections(text)
    
    # Use recursive splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    
    chunks = text_splitter.split_text(text)
    
    # Create chunk metadata with section information
    chunk_metadatas = []
    current_section = "general"
    section_index = 0
    
    for i, chunk in enumerate(chunks):
        # Find which section this chunk belongs to
        chunk_start_pos = text.find(chunk)
        if chunk_start_pos >= 0:
            # Find the last section before this chunk
            for sec_pos, sec_heading, sec_type in sections:
                if sec_pos * 50 < chunk_start_pos:  # Rough estimate
                    current_section = sec_type
                else:
                    break
        
        # Extract section from chunk content as fallback
        detected_section = extract_section_from_content(chunk)
        if detected_section != "general":
            current_section = detected_section
        
        chunk_metadatas.append({
            "section": current_section,
            "chunk_index": i,
        })
    
    return list(zip(chunks, chunk_metadatas))


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Split text into chunks for embedding (legacy function for compatibility)."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    return chunks


def process_pdf_for_rag(
    file_path: str,
    filename: Optional[str] = None,
    document_type: Optional[str] = None,
    destination: Optional[str] = None
) -> Tuple[List[str], List[Dict[str, any]]]:
    """
    Process PDF file and return text chunks with metadata.
    
    Args:
        file_path: Path to PDF file
        filename: Original filename (if different from file_path)
        document_type: Document type (if None, will be classified)
        destination: Destination name (if None, will be extracted)
    
    Returns:
        Tuple of (chunks, metadatas)
    """
    if filename is None:
        filename = Path(file_path).name
    
    # Load PDF
    text, pdf_info = load_pdf(file_path)
    
    if not text.strip():
        return [], []
    
    # Get content preview for classification
    content_preview = text[:1000]
    
    # Classify document and extract metadata
    if document_type is None:
        document_type = classify_document_type(filename, content_preview)
    
    if destination is None:
        destination = extract_destination_from_filename(filename)
        if not destination:
            destination = extract_destination_from_content(text)
    
    # Create document metadata
    doc_metadata = create_document_metadata(
        filename=filename,
        document_type=document_type,
        destination=destination,
        content_preview=content_preview
    )
    
    # Chunk text with sections
    chunk_data = chunk_text_with_sections(text, document_type=document_type)
    
    chunks = []
    metadatas = []
    
    for i, (chunk_text, chunk_info) in enumerate(chunk_data):
        chunks.append(chunk_text)
        
        # Create chunk metadata
        chunk_metadata = create_chunk_metadata(
            document_metadata=doc_metadata,
            chunk_number=i,
            chunk_text=chunk_text,
            page_number=None  # Could be enhanced to track page numbers
        )
        
        # Merge section info
        chunk_metadata.update(chunk_info)
        metadatas.append(chunk_metadata)
    
    return chunks, metadatas

