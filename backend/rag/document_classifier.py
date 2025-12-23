"""Document type classification and metadata extraction for travel documents."""

import re
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime


def classify_document_type(filename: str, content_preview: str = "") -> str:
    """
    Classify document type based on filename and content.
    
    Args:
        filename: Name of the document file
        content_preview: First 1000 characters of document content
        
    Returns:
        Document type: travel_guide, destination_info, restaurant_guide, hotel_guide, transport_guide
    """
    filename_lower = filename.lower()
    content_lower = content_preview.lower() if content_preview else ""
    
    # Check filename patterns
    if any(keyword in filename_lower for keyword in ["restaurant", "dining", "food", "eat", "cuisine"]):
        return "restaurant_guide"
    
    if any(keyword in filename_lower for keyword in ["hotel", "accommodation", "lodging", "stay"]):
        return "hotel_guide"
    
    if any(keyword in filename_lower for keyword in ["transport", "transit", "airport", "train", "bus", "metro"]):
        return "transport_guide"
    
    if any(keyword in filename_lower for keyword in ["guide", "travel", "destination", "city", "country"]):
        # Check if it's a general travel guide or specific destination info
        if any(keyword in filename_lower for keyword in ["lonely", "rick", "fodor", "rough", "frommer"]):
            return "travel_guide"
        return "destination_info"
    
    # Check content patterns if filename doesn't help
    if content_preview:
        if any(keyword in content_lower for keyword in ["restaurant", "dining", "cuisine", "menu", "food"]):
            if "hotel" not in content_lower[:500]:  # Prioritize restaurant if both appear
                return "restaurant_guide"
        
        if any(keyword in content_lower for keyword in ["hotel", "accommodation", "lodging", "check-in"]):
            return "hotel_guide"
        
        if any(keyword in content_lower for keyword in ["transport", "airport", "train station", "metro", "subway"]):
            return "transport_guide"
    
    # Default to travel guide for general travel content
    return "travel_guide"


def extract_destination_from_filename(filename: str) -> Optional[str]:
    """
    Extract destination name from filename.
    
    Args:
        filename: Name of the document file
        
    Returns:
        Destination name or None if not found
    """
    # Remove extension
    name = Path(filename).stem.lower()
    
    # Common destination patterns (cities and countries)
    destinations = [
        # Cities
        "tokyo", "paris", "london", "new york", "barcelona", "rome", "amsterdam",
        "berlin", "dublin", "prague", "vienna", "budapest", "lisbon", "athens",
        "istanbul", "dubai", "singapore", "hong kong", "bangkok", "seoul",
        "sydney", "melbourne", "auckland", "rio", "buenos aires", "mexico city",
        "san francisco", "los angeles", "chicago", "miami", "boston", "seattle",
        "zurich", "geneva", "bern", "basel", "lausanne", "lucerne", "interlaken",
        "zermatt", "st. moritz", "st moritz",
        # Countries
        "japan", "france", "italy", "spain", "germany", "uk", "england",
        "switzerland", "austria", "belgium", "netherlands", "portugal", "greece",
        "thailand", "vietnam", "indonesia", "philippines", "india", "china"
    ]
    
    # Check for destination in filename
    for dest in destinations:
        if dest in name:
            # Capitalize properly
            if " " in dest:
                return dest.title()
            return dest.capitalize()
    
    # Try to extract from patterns like "tokyo_guide" or "paris-travel"
    patterns = [
        r"^([a-z]+(?:[-_][a-z]+)*)",  # First word before separator
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",  # Capitalized words
    ]
    
    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            candidate = match.group(1).replace("_", " ").replace("-", " ").title()
            # Filter out common non-destination words
            if candidate.lower() not in ["travel", "guide", "the", "a", "an"]:
                return candidate
    
    return None


def extract_destination_from_content(content: str, max_chars: int = 2000) -> Optional[str]:
    """
    Extract destination name from document content.
    Handles multiple destinations and document references.
    
    Args:
        content: Document content or query text
        max_chars: Maximum characters to analyze
        
    Returns:
        Destination name or None if not found. Returns the first/primary destination found.
        For queries with multiple destinations, returns the most specific one (city over country).
    """
    preview = content[:max_chars]
    preview_lower = preview.lower()
    
    # First, try to extract from document reference patterns (e.g., "Switzerland travel guide")
    document_patterns = [
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+travel\s+guide",
        r"travel\s+guide\s+(?:to\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+guide",
        r"guide\s+(?:to\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+pdf",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+document",
    ]
    
    for pattern in document_patterns:
        match = re.search(pattern, preview, re.IGNORECASE)
        if match:
            dest = match.group(1)
            # Validate it's a known destination
            if _is_known_destination(dest):
                return dest.title() if " " in dest else dest.capitalize()
    
    # Look for common patterns (case-insensitive)
    patterns = [
        r"travel guide to ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"visiting ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?) travel",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?) guide",
        r"guide to ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, preview, re.IGNORECASE)
        if match:
            dest = match.group(1)
            if _is_known_destination(dest):
                return dest.title() if " " in dest else dest.capitalize()
    
    # Check for multiple destinations (e.g., "Zurich and Switzerland")
    # Extract all mentioned destinations and return the most specific one
    all_destinations = extract_all_destinations(preview_lower)
    if all_destinations:
        # Prefer cities over countries (more specific)
        cities = [d for d in all_destinations if _is_city(d)]
        if cities:
            return cities[0].title() if " " in cities[0] else cities[0].capitalize()
        # Otherwise return first destination found
        return all_destinations[0].title() if " " in all_destinations[0] else all_destinations[0].capitalize()
    
    return None


def _is_known_destination(name: str) -> bool:
    """Check if a name is a known destination."""
    name_lower = name.lower()
    known_destinations = [
        # Cities
        "tokyo", "paris", "london", "new york", "barcelona", "rome", "amsterdam",
        "berlin", "dublin", "prague", "vienna", "budapest", "lisbon", "athens",
        "istanbul", "dubai", "singapore", "hong kong", "bangkok", "seoul",
        "sydney", "melbourne", "auckland", "rio", "buenos aires", "mexico city",
        "san francisco", "los angeles", "chicago", "miami", "boston", "seattle",
        "zurich", "geneva", "bern", "basel", "lausanne", "lucerne", "interlaken",
        "zermatt", "st. moritz", "st moritz", "jungfrau region",
        # Countries
        "japan", "france", "italy", "spain", "germany", "uk", "england", "united kingdom",
        "switzerland", "austria", "belgium", "netherlands", "portugal", "greece",
        "thailand", "vietnam", "indonesia", "philippines", "india", "china",
    ]
    return name_lower in known_destinations


def _is_city(name: str) -> bool:
    """Check if a destination is a city (not a country)."""
    name_lower = name.lower()
    cities = [
        "tokyo", "paris", "london", "new york", "barcelona", "rome", "amsterdam",
        "berlin", "dublin", "prague", "vienna", "budapest", "lisbon", "athens",
        "istanbul", "dubai", "singapore", "hong kong", "bangkok", "seoul",
        "sydney", "melbourne", "auckland", "rio", "buenos aires", "mexico city",
        "san francisco", "los angeles", "chicago", "miami", "boston", "seattle",
        "zurich", "geneva", "bern", "basel", "lausanne", "lucerne", "interlaken",
        "zermatt", "st. moritz", "st moritz", "jungfrau region",
    ]
    return name_lower in cities


def extract_all_destinations(text: str) -> List[str]:
    """
    Extract all destination names mentioned in text.
    Handles patterns like "Zurich and Switzerland", "Tokyo, Japan", etc.
    """
    destinations = []
    text_lower = text.lower()
    
    # Known destinations list (same as in _is_known_destination)
    known_destinations = [
        # Cities
        "tokyo", "paris", "london", "new york", "barcelona", "rome", "amsterdam",
        "berlin", "dublin", "prague", "vienna", "budapest", "lisbon", "athens",
        "istanbul", "dubai", "singapore", "hong kong", "bangkok", "seoul",
        "sydney", "melbourne", "auckland", "rio", "buenos aires", "mexico city",
        "san francisco", "los angeles", "chicago", "miami", "boston", "seattle",
        "zurich", "geneva", "bern", "basel", "lausanne", "lucerne", "interlaken",
        "zermatt", "st. moritz", "st moritz", "jungfrau region",
        # Countries
        "japan", "france", "italy", "spain", "germany", "uk", "england", "united kingdom",
        "switzerland", "austria", "belgium", "netherlands", "portugal", "greece",
        "thailand", "vietnam", "indonesia", "philippines", "india", "china",
    ]
    
    # Check for each destination in the text
    for dest in known_destinations:
        # Use word boundaries to avoid partial matches (e.g., "switzerland" not matching "swiss")
        pattern = r'\b' + re.escape(dest) + r'\b'
        if re.search(pattern, text_lower):
            # Capitalize properly
            if " " in dest:
                destinations.append(dest.title())
            else:
                destinations.append(dest.capitalize())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_destinations = []
    for dest in destinations:
        dest_lower = dest.lower()
        if dest_lower not in seen:
            seen.add(dest_lower)
            unique_destinations.append(dest)
    
    return unique_destinations


def extract_section_from_content(chunk_text: str) -> str:
    """
    Classify the section type of a chunk based on content.
    
    Args:
        chunk_text: Text content of the chunk
        
    Returns:
        Section type: attractions, restaurants, hotels, transport, culture, tips, general
    """
    text_lower = chunk_text.lower()
    
    # Check for section indicators
    if any(keyword in text_lower for keyword in ["restaurant", "dining", "cuisine", "food", "eat", "menu", "cafe", "bar"]):
        return "restaurants"
    
    if any(keyword in text_lower for keyword in ["hotel", "accommodation", "lodging", "stay", "check-in", "resort"]):
        return "hotels"
    
    if any(keyword in text_lower for keyword in ["transport", "airport", "train", "bus", "metro", "subway", "taxi", "getting around"]):
        return "transport"
    
    if any(keyword in text_lower for keyword in ["attraction", "sight", "monument", "museum", "landmark", "must-see", "visit"]):
        return "attractions"
    
    if any(keyword in text_lower for keyword in ["culture", "tradition", "custom", "festival", "history", "heritage"]):
        return "culture"
    
    if any(keyword in text_lower for keyword in ["tip", "advice", "recommendation", "should know", "important", "note"]):
        return "tips"
    
    return "general"


def create_document_metadata(
    filename: str,
    document_type: Optional[str] = None,
    destination: Optional[str] = None,
    content_preview: str = ""
) -> Dict[str, any]:
    """
    Create comprehensive metadata for a document with hierarchical destination information.
    
    Args:
        filename: Name of the document file
        document_type: Document type (if None, will be classified)
        destination: Destination name (if None, will be extracted)
        content_preview: First 1000 characters of content
        
    Returns:
        Dictionary with document metadata including hierarchical destination info
    """
    if document_type is None:
        document_type = classify_document_type(filename, content_preview)
    
    if destination is None:
        destination = extract_destination_from_filename(filename)
        if not destination and content_preview:
            destination = extract_destination_from_content(content_preview)
    
    # Extract year from filename if present
    year_match = re.search(r"20\d{2}", filename)
    year = year_match.group(0) if year_match else str(datetime.now().year)
    
    # Create document ID from filename and destination
    doc_id = f"{destination.lower().replace(' ', '-') if destination else 'unknown'}-{Path(filename).stem.lower()}"
    doc_id = re.sub(r"[^a-z0-9-]", "", doc_id)
    
    metadata = {
        "document_id": doc_id,
        "document_title": Path(filename).stem.replace("_", " ").replace("-", " ").title(),
        "document_type": document_type,
        "source_file": filename,
        "upload_date": datetime.now().strftime("%Y-%m-%d"),
        "year": year,
    }
    
    # Add hierarchical destination metadata
    if destination:
        metadata["destination"] = destination
        metadata["destinations"] = [destination]  # Can be expanded for multi-destination docs
        
        # Try to determine if destination is a city or country
        # Import here to avoid circular dependency
        try:
            from rag.retriever import get_country_from_city
            country = get_country_from_city(destination)
            if country:
                # Destination is a city, store both city and country
                metadata["city"] = destination
                metadata["country"] = country
            else:
                # Destination might be a country, check if any cities map to it
                # For now, store as country
                metadata["country"] = destination
        except ImportError:
            # If import fails, just store destination
            pass
    
    return metadata


def create_chunk_metadata(
    document_metadata: Dict[str, any],
    chunk_number: int,
    chunk_text: str,
    page_number: Optional[int] = None
) -> Dict[str, any]:
    """
    Create metadata for a document chunk.
    
    Args:
        document_metadata: Base document metadata
        chunk_number: Chunk index number
        chunk_text: Text content of the chunk
        page_number: Page number if available
        
    Returns:
        Dictionary with chunk metadata
    """
    chunk_metadata = document_metadata.copy()
    chunk_metadata.update({
        "chunk_number": chunk_number,
        "chunk_text": chunk_text,
        "section": extract_section_from_content(chunk_text),
    })
    
    if page_number is not None:
        chunk_metadata["page_number"] = page_number
    
    return chunk_metadata

