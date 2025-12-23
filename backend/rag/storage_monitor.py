"""Storage usage monitoring for Pinecone indexes."""

from typing import Dict, Optional
from pinecone import Pinecone
from config import config


def get_storage_usage(pc: Pinecone, index_name: str) -> Dict[str, any]:
    """
    Get storage usage statistics for an index.
    
    Args:
        pc: Pinecone client instance
        index_name: Name of the index
        
    Returns:
        Dictionary with storage statistics
    """
    try:
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        
        total_vectors = stats.get("total_vector_count", 0)
        dimension = stats.get("dimension", 1536)
        
        estimated_storage_bytes = total_vectors * (dimension * 4 + 1024)
        estimated_storage_mb = estimated_storage_bytes / (1024 * 1024)
        estimated_storage_gb = estimated_storage_mb / 1024
        
        return {
            "total_vectors": total_vectors,
            "dimension": dimension,
            "namespaces": stats.get("namespaces", {}),
            "estimated_storage_mb": round(estimated_storage_mb, 2),
            "estimated_storage_gb": round(estimated_storage_gb, 4),
            "index_fullness": stats.get("index_fullness", 0),
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_vectors": 0,
            "estimated_storage_gb": 0,
        }


def check_storage_quota(index_name: str, warning_threshold_gb: float = 1.5) -> Dict[str, any]:
    """
    Check if storage is approaching the limit.
    
    Args:
        index_name: Name of the index
        warning_threshold_gb: Warning threshold in GB (default 1.5 GB for 2 GB limit)
        
    Returns:
        Dictionary with quota status
    """
    if not config.PINECONE_API_KEY:
        return {
            "error": "PINECONE_API_KEY not configured",
            "within_quota": False,
        }
    
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    stats = get_storage_usage(pc, index_name)
    
    if "error" in stats:
        return stats
    
    storage_gb = stats["estimated_storage_gb"]
    limit_gb = 2.0
    
    within_quota = storage_gb < limit_gb
    warning = storage_gb >= warning_threshold_gb
    usage_percent = (storage_gb / limit_gb) * 100
    
    return {
        **stats,
        "within_quota": within_quota,
        "warning": warning,
        "usage_percent": round(usage_percent, 2),
        "limit_gb": limit_gb,
        "remaining_gb": round(limit_gb - storage_gb, 4),
    }


def estimate_upload_size(num_chunks: int, dimension: int = 1536, avg_metadata_size: int = 500) -> Dict[str, float]:
    """
    Estimate storage size for an upload.
    
    Args:
        num_chunks: Number of chunks to upload
        dimension: Vector dimension
        avg_metadata_size: Average metadata size in bytes
        
    Returns:
        Dictionary with size estimates
    """
    vector_size = dimension * 4
    
    chunk_size_bytes = vector_size + avg_metadata_size + 512
    
    total_bytes = num_chunks * chunk_size_bytes
    total_mb = total_bytes / (1024 * 1024)
    total_gb = total_mb / 1024
    
    return {
        "estimated_size_mb": round(total_mb, 2),
        "estimated_size_gb": round(total_gb, 4),
        "chunks": num_chunks,
    }


def can_upload(index_name: str, estimated_chunks: int, dimension: int = 1536) -> Dict[str, any]:
    """
    Check if an upload would exceed storage quota.
    
    Args:
        index_name: Name of the index
        estimated_chunks: Estimated number of chunks to upload
        dimension: Vector dimension
        
    Returns:
        Dictionary with upload feasibility
    """
    quota_status = check_storage_quota(index_name)
    
    if "error" in quota_status:
        return {
            "can_upload": False,
            "reason": quota_status["error"],
        }
    
    upload_estimate = estimate_upload_size(estimated_chunks, dimension)
    current_usage_gb = quota_status["estimated_storage_gb"]
    estimated_additional_gb = upload_estimate["estimated_size_gb"]
    total_after_upload = current_usage_gb + estimated_additional_gb
    
    can_upload = total_after_upload < 2.0
    warning = total_after_upload >= 1.5
    
    return {
        "can_upload": can_upload,
        "warning": warning,
        "current_usage_gb": current_usage_gb,
        "estimated_additional_gb": estimated_additional_gb,
        "total_after_upload_gb": round(total_after_upload, 4),
        "remaining_after_upload_gb": round(2.0 - total_after_upload, 4),
        "upload_estimate": upload_estimate,
    }

