"""Centralized configuration module for environment variables."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

backend_dir = Path(__file__).parent
env_path = backend_dir / ".env"
load_dotenv(env_path)


class Config:
    """Centralized configuration class for all environment variables."""
    
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: Optional[str] = os.getenv("PINECONE_ENVIRONMENT") or None
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "paradise-travel-index")
    SERPAPI_API_KEY: Optional[str] = os.getenv("SERPAPI_API_KEY") or None
    GOOGLE_PLACES_API_KEY: Optional[str] = os.getenv("GOOGLE_PLACES_API_KEY") or None
    PDF_PATH: str = os.getenv("PDF_PATH", "data/switzerland_travel_guide.pdf")
    
    @classmethod
    def validate_required(cls) -> list[str]:
        """
        Validate that all required environment variables are set.
        
        Returns:
            List of missing required variable names
        """
        required_vars = {
            "LIVEKIT_URL": cls.LIVEKIT_URL,
            "LIVEKIT_API_KEY": cls.LIVEKIT_API_KEY,
            "LIVEKIT_API_SECRET": cls.LIVEKIT_API_SECRET,
            "OPENAI_API_KEY": cls.OPENAI_API_KEY,
        }
        
        missing = [var for var, value in required_vars.items() if not value]
        return missing
    
    @classmethod
    def is_rag_enabled(cls) -> bool:
        """Check if RAG is enabled (Pinecone configured)."""
        return bool(cls.PINECONE_API_KEY)
    
    @classmethod
    def are_tools_enabled(cls) -> bool:
        """Check if external tools are enabled (SerpAPI or Google Places configured)."""
        return bool(cls.SERPAPI_API_KEY or cls.GOOGLE_PLACES_API_KEY)


config = Config()

