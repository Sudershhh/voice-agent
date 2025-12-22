"""Pinecone retriever for RAG pipeline."""

import os
from typing import List
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings


def initialize_pinecone() -> Pinecone:
    """Initialize Pinecone client."""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable not set")
    
    pc = Pinecone(api_key=api_key)
    return pc


def get_or_create_index(pc: Pinecone, index_name: str, dimension: int = 1536):
    """Get existing index or create a new one."""
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    
    return pc.Index(index_name)


def create_vector_store(index_name: str) -> PineconeVectorStore:
    """Create a Pinecone vector store for RAG."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    pc = initialize_pinecone()
    index = get_or_create_index(pc, index_name, dimension=1536)
    
    vector_store = PineconeVectorStore(
        index=index,
        embedding=embeddings,
    )
    
    return vector_store


def add_documents_to_vector_store(vector_store: PineconeVectorStore, texts: List[str], metadatas: List[dict] = None):
    """Add documents to the vector store."""
    if metadatas is None:
        metadatas = [{}] * len(texts)
    
    vector_store.add_texts(texts=texts, metadatas=metadatas)


def get_retriever(vector_store: PineconeVectorStore, k: int = 4):
    """Get a retriever from the vector store."""
    return vector_store.as_retriever(search_kwargs={"k": k})

