"""Pinecone retriever for RAG pipeline."""

from typing import List, Optional, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain.schema import BaseRetriever
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.schema import Document
from config import config


def initialize_pinecone() -> Pinecone:
    """Initialize Pinecone client."""
    if not config.PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY environment variable not set")
    
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    return pc


def get_or_create_index(pc: Pinecone, index_name: str, dimension: int = 1536):
    """Get existing index or create a new one."""
    existing_indexes = pc.list_indexes()
    index_names = [idx.name for idx in existing_indexes.indexes] if hasattr(existing_indexes, 'indexes') else existing_indexes.names()
    
    if index_name not in index_names:
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


def create_vector_store(index_name: str, namespace: Optional[str] = None) -> PineconeVectorStore:
    """
    Create a Pinecone vector store for RAG.
    
    Args:
        index_name: Name of the Pinecone index
        namespace: Optional namespace for organizing documents
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    pc = initialize_pinecone()
    index = get_or_create_index(pc, index_name, dimension=1536)
    
    vector_store = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        namespace=namespace,
    )
    
    return vector_store


# City to country mapping for hierarchical namespace search
CITY_TO_COUNTRY = {
    # Switzerland cities
    "zurich": "switzerland",
    "geneva": "switzerland",
    "bern": "switzerland",
    "basel": "switzerland",
    "lausanne": "switzerland",
    "lucerne": "switzerland",
    "interlaken": "switzerland",
    "zermatt": "switzerland",
    "st. moritz": "switzerland",
    "st moritz": "switzerland",
    # France cities
    "paris": "france",
    "lyon": "france",
    "marseille": "france",
    "nice": "france",
    "bordeaux": "france",
    # Italy cities
    "rome": "italy",
    "milan": "italy",
    "venice": "italy",
    "florence": "italy",
    "naples": "italy",
    # Germany cities
    "berlin": "germany",
    "munich": "germany",
    "hamburg": "germany",
    "frankfurt": "germany",
    # Spain cities
    "madrid": "spain",
    "barcelona": "spain",
    "seville": "spain",
    "valencia": "spain",
    # UK cities
    "london": "united kingdom",
    "edinburgh": "united kingdom",
    "manchester": "united kingdom",
    # Japan cities
    "tokyo": "japan",
    "osaka": "japan",
    "kyoto": "japan",
    # Add more as needed
}


def get_country_from_city(city: str) -> Optional[str]:
    """
    Get country name from city name using mapping.
    
    Args:
        city: City name (case-insensitive)
        
    Returns:
        Country name or None if not found
    """
    city_normalized = city.lower().strip()
    return CITY_TO_COUNTRY.get(city_normalized)


def get_namespace_for_destination(destination: Optional[str]) -> str:
    """
    Get namespace name for a destination.
    
    Args:
        destination: Destination name or None
        
    Returns:
        Namespace name (default: "general" if no destination)
    """
    if not destination:
        return "general"
    
    # Normalize destination name for namespace
    namespace = destination.lower().replace(" ", "-").replace("_", "-")
    # Remove special characters
    namespace = "".join(c for c in namespace if c.isalnum() or c == "-")
    # Limit length
    if len(namespace) > 50:
        namespace = namespace[:50]
    
    return namespace


def get_hierarchical_namespaces(destination: Optional[str]) -> List[str]:
    """
    Get hierarchical list of namespaces to search (city → country → general).
    
    Args:
        destination: Destination name (could be city or country)
        
    Returns:
        List of namespaces to search in order of preference
    """
    if not destination:
        return ["general"]
    
    namespaces = []
    dest_normalized = destination.lower().strip()
    
    # Add the destination itself as first namespace
    dest_namespace = get_namespace_for_destination(destination)
    if dest_namespace not in namespaces:
        namespaces.append(dest_namespace)
    
    # If destination is a city, add its country namespace
    country = get_country_from_city(dest_normalized)
    if country:
        country_namespace = get_namespace_for_destination(country)
        if country_namespace not in namespaces:
            namespaces.append(country_namespace)
    
    # Always add general as fallback
    if "general" not in namespaces:
        namespaces.append("general")
    
    return namespaces


def add_documents_to_vector_store(
    vector_store: PineconeVectorStore,
    texts: List[str],
    metadatas: List[dict] = None,
    namespace: Optional[str] = None
):
    """
    Add documents to the vector store.
    
    Args:
        vector_store: Pinecone vector store instance
        texts: List of text chunks
        metadatas: List of metadata dictionaries
        namespace: Optional namespace (if None, uses vector_store namespace)
    """
    # #region debug log
    import json
    log_data = {
        "sessionId": "debug-session",
        "runId": "post-fix",
        "hypothesisId": "FIX",
        "location": "retriever.py:add_documents_to_vector_store:entry",
        "message": "Function entry - post-fix",
        "data": {
            "texts_count": len(texts) if texts else 0,
            "metadatas_count": len(metadatas) if metadatas else 0,
            "namespace": namespace,
            "vector_store_type": type(vector_store).__name__,
        },
        "timestamp": __import__("time").time() * 1000
    }
    try:
        with open(r"c:\Users\tgsud\Desktop\voice-agent\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data) + "\n")
    except: pass
    # #endregion
    
    if metadatas is None:
        metadatas = [{}] * len(texts)
    
    # Ensure all chunks have required metadata fields
    for i, metadata in enumerate(metadatas):
        if "chunk_number" not in metadata:
            metadata["chunk_number"] = i
    
    # If namespace is provided, create a new vector store instance with that namespace
    # PineconeVectorStore doesn't allow changing namespace after initialization
    if namespace:
        # #region debug log
        log_data = {
            "sessionId": "debug-session",
            "runId": "post-fix-v2",
            "hypothesisId": "E",
            "location": "retriever.py:add_documents_to_vector_store:inspecting_vector_store",
            "message": "Inspecting vector store attributes",
            "data": {
                "namespace": namespace,
                "vector_store_attrs": [attr for attr in dir(vector_store) if not attr.startswith("_")][:20],
                "has_index": hasattr(vector_store, "index"),
                "has_embedding": hasattr(vector_store, "embedding"),
            },
            "timestamp": __import__("time").time() * 1000
        }
        try:
            with open(r"c:\Users\tgsud\Desktop\voice-agent\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except: pass
        # #endregion
        
        # Get index and create new embeddings instance
        # PineconeVectorStore doesn't expose embedding as attribute, so we recreate it
        try:
            index = vector_store.index
            # #region debug log
            log_data = {
                "sessionId": "debug-session",
                "runId": "post-fix-v2",
                "hypothesisId": "E",
                "location": "retriever.py:add_documents_to_vector_store:got_index",
                "message": "Successfully got index",
                "data": {"index_type": type(index).__name__},
                "timestamp": __import__("time").time() * 1000
            }
            try:
                with open(r"c:\Users\tgsud\Desktop\voice-agent\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_data) + "\n")
            except: pass
            # #endregion
        except AttributeError as e:
            # #region debug log
            log_data = {
                "sessionId": "debug-session",
                "runId": "post-fix-v2",
                "hypothesisId": "E",
                "location": "retriever.py:add_documents_to_vector_store:index_error",
                "message": "Failed to get index",
                "data": {"error": str(e)},
                "timestamp": __import__("time").time() * 1000
            }
            try:
                with open(r"c:\Users\tgsud\Desktop\voice-agent\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_data) + "\n")
            except: pass
            # #endregion
            raise
        
        # Create new embeddings instance (same model as used in create_vector_store)
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Create a new vector store instance with the specified namespace
        namespace_vector_store = PineconeVectorStore(
            index=index,
            embedding=embeddings,
            namespace=namespace,
        )
        
        # #region debug log
        log_data = {
            "sessionId": "debug-session",
            "runId": "post-fix-v2",
            "hypothesisId": "E",
            "location": "retriever.py:add_documents_to_vector_store:created_new_store",
            "message": "Created new vector store with namespace",
            "data": {"namespace": namespace},
            "timestamp": __import__("time").time() * 1000
        }
        try:
            with open(r"c:\Users\tgsud\Desktop\voice-agent\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except: pass
        # #endregion
        
        namespace_vector_store.add_texts(texts=texts, metadatas=metadatas)
        
        # #region debug log
        log_data = {
            "sessionId": "debug-session",
            "runId": "post-fix",
            "hypothesisId": "FIX",
            "location": "retriever.py:add_documents_to_vector_store:namespace_add_success",
            "message": "Successfully added texts with namespace",
            "data": {"texts_count": len(texts), "namespace": namespace},
            "timestamp": __import__("time").time() * 1000
        }
        try:
            with open(r"c:\Users\tgsud\Desktop\voice-agent\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except: pass
        # #endregion
    else:
        # #region debug log
        log_data = {
            "sessionId": "debug-session",
            "runId": "post-fix",
            "hypothesisId": "FIX",
            "location": "retriever.py:add_documents_to_vector_store:no_namespace_branch",
            "message": "No namespace provided, using existing vector store",
            "data": {},
            "timestamp": __import__("time").time() * 1000
        }
        try:
            with open(r"c:\Users\tgsud\Desktop\voice-agent\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except: pass
        # #endregion
        vector_store.add_texts(texts=texts, metadatas=metadatas)
        
        # #region debug log
        log_data = {
            "sessionId": "debug-session",
            "runId": "post-fix",
            "hypothesisId": "FIX",
            "location": "retriever.py:add_documents_to_vector_store:default_add_success",
            "message": "Successfully added texts without namespace",
            "data": {"texts_count": len(texts)},
            "timestamp": __import__("time").time() * 1000
        }
        try:
            with open(r"c:\Users\tgsud\Desktop\voice-agent\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except: pass
        # #endregion


class FilteredRetriever(BaseRetriever):
    """Retriever with metadata filtering support."""
    
    k: int = 4
    filter: Optional[Dict[str, Any]] = None
    namespace: Optional[str] = None
    additional_namespaces: Optional[List[str]] = None
    
    def __init__(
        self,
        vector_store: PineconeVectorStore,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
        additional_namespaces: Optional[List[str]] = None,
        **kwargs
    ):
        # Initialize parent without vector_store (it's not a Pydantic field)
        super().__init__(**kwargs)
        
        # Store vector_store as a private attribute (not a Pydantic field)
        self._vector_store = vector_store
        self.k = k
        self.filter = filter
        self.namespace = namespace
        self.additional_namespaces = additional_namespaces or []
    
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        """Retrieve documents with optional filtering and hierarchical namespace search."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            search_kwargs = {"k": self.k}
            
            if self.filter:
                search_kwargs["filter"] = self.filter
            
            # Determine namespaces to search (hierarchical: city → country → general)
            # Also include additional namespaces for multi-destination queries
            namespaces_to_try = []
            seen_namespaces = set()
            
            if self.namespace:
                # Convert namespace back to destination name (replace hyphens with spaces)
                destination_from_namespace = self.namespace.replace("-", " ").title()
                # Get hierarchical namespaces based on primary destination
                primary_namespaces = get_hierarchical_namespaces(destination_from_namespace)
                for ns in primary_namespaces:
                    if ns not in seen_namespaces:
                        namespaces_to_try.append(ns)
                        seen_namespaces.add(ns)
            
            # Add additional namespaces (for multi-destination queries like "Zurich and Switzerland")
            for additional_dest in self.additional_namespaces:
                if additional_dest:
                    # Get hierarchical namespaces for each additional destination
                    additional_ns_list = get_hierarchical_namespaces(additional_dest)
                    for ns in additional_ns_list:
                        if ns not in seen_namespaces:
                            namespaces_to_try.append(ns)
                            seen_namespaces.add(ns)
            
            # If no namespaces specified, default to general
            if not namespaces_to_try:
                namespaces_to_try = ["general"]
            
            # Try each namespace in order until we find results
            all_docs = []
            seen_ids = set()  # Deduplicate across namespaces
            
            for namespace in namespaces_to_try:
                try:
                    # Create a new vector store instance with the namespace
                    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                    temp_vector_store = PineconeVectorStore(
                        index=self._vector_store.index,
                        embedding=embeddings,
                        namespace=namespace,
                    )
                    retriever = temp_vector_store.as_retriever(search_kwargs=search_kwargs)
                    
                    namespace_docs = retriever.invoke(query)
                    
                    # Deduplicate by document content (first 100 chars as ID)
                    for doc in namespace_docs:
                        doc_id = doc.page_content[:100] if doc.page_content else str(doc.metadata.get("chunk_number", ""))
                        if doc_id not in seen_ids:
                            seen_ids.add(doc_id)
                            all_docs.append(doc)
                    
                    # If we found results in this namespace, we can stop (or continue for more diversity)
                    # For now, we'll collect from all namespaces and return top k
                    logger.debug(f"Found {len(namespace_docs)} docs in namespace '{namespace}'")
                    
                except Exception as namespace_error:
                    logger.warning(f"Error searching namespace '{namespace}': {str(namespace_error)}")
                    continue
            
            # If no namespace specified, try default retriever
            if not self.namespace and not all_docs:
                retriever = self._vector_store.as_retriever(search_kwargs=search_kwargs)
                all_docs = retriever.invoke(query)
            
            # Return top k results
            return all_docs[:self.k]
            
        except Exception as e:
            # Log error for debugging
            logger.error(f"Error retrieving documents: {str(e)}", exc_info=True)
            # Return empty list on error rather than crashing
            return []


def get_retriever(
    vector_store: PineconeVectorStore,
    k: int = 4,
    filter: Optional[Dict[str, Any]] = None,
    namespace: Optional[str] = None,
    additional_namespaces: Optional[List[str]] = None,
) -> BaseRetriever:
    """
    Get a retriever from the vector store with optional filtering.
    
    Args:
        vector_store: Pinecone vector store
        k: Number of documents to retrieve
        filter: Optional metadata filter dictionary
        namespace: Optional primary namespace to search in
        additional_namespaces: Optional list of additional namespaces to try (for multi-destination queries)
    
    Returns:
        Retriever instance
    """
    if filter or namespace or additional_namespaces:
        return FilteredRetriever(
            vector_store=vector_store,
            k=k,
            filter=filter,
            namespace=namespace,
            additional_namespaces=additional_namespaces,
        )
    else:
        return vector_store.as_retriever(search_kwargs={"k": k})


def create_metadata_filter(
    destination: Optional[str] = None,
    document_type: Optional[str] = None,
    section: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Create a metadata filter for queries.
    
    Args:
        destination: Filter by destination
        document_type: Filter by document type
        section: Filter by section type
    
    Returns:
        Filter dictionary or None
    """
    filters = []
    
    if destination:
        filters.append({"destination": {"$eq": destination}})
    
    if document_type:
        filters.append({"document_type": {"$eq": document_type}})
    
    if section:
        filters.append({"section": {"$eq": section}})
    
    if not filters:
        return None
    
    if len(filters) == 1:
        return filters[0]
    
    return {"$and": filters}

