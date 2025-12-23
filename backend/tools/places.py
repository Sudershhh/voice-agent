"""Places search tool using Google Places API."""

from typing import Dict, List, Optional
import googlemaps
from config import config


def search_places(
    query: str,
    location: Optional[str] = None,
    place_type: Optional[str] = None,
    max_results: int = 5
) -> Dict:
    """
    Search for places using Google Places API.
    
    Args:
        query: Search query (e.g., "cozy cafes", "restaurants", "hotels", "attractions")
        location: Location to search near (optional, extract from conversation if mentioned)
        place_type: Type of place (e.g., "cafe", "restaurant", "hotel", "tourist_attraction")
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        Dictionary with place information including names, ratings, reviews, addresses
    """
    
    api_key = config.GOOGLE_PLACES_API_KEY
    if not api_key:
        error_result = {
            "error": "GOOGLE_PLACES_API_KEY not configured",
            "places": []
        }
        return error_result
    
    try:
        gmaps = googlemaps.Client(key=api_key)
        
        search_query = query
        if location:
            search_query = f"{query} in {location}"
        if place_type:
            search_query += f" {place_type}"
        
        places_result = gmaps.places(query=search_query)
        
        if "status" in places_result:
            status = places_result.get("status")
            if status != "OK" and status != "ZERO_RESULTS":
                error_msg = f"Google Places API returned status: {status}"
                if "error_message" in places_result:
                    error_msg += f" - {places_result['error_message']}"
                if status != "ZERO_RESULTS":
                    raise Exception(error_msg)
        
        places = []
        results = places_result.get("results", [])
        
        for place in results[:max_results]:
            place_id = place.get("place_id")
            if not place_id:
                continue
            
            try:
                place_details = gmaps.place(
                    place_id=place_id,
                    fields=["name", "rating", "reviews", "formatted_address", "geometry", "types"]
                )
                details = place_details.get("result", {})
                
                reviews = []
                for review in details.get("reviews", [])[:5]:
                    reviews.append({
                        "author": review.get("author_name", "Anonymous"),
                        "rating": review.get("rating", 0),
                        "text": review.get("text", "")[:200]
                    })
                
                geometry = details.get("geometry", {})
                location_coords = None
                if "location" in geometry:
                    loc = geometry["location"]
                    location_coords = {
                        "lat": loc.get("lat"),
                        "lng": loc.get("lng")
                    }
                
                place_info = {
                    "name": details.get("name", place.get("name", "Unknown")),
                    "rating": details.get("rating", place.get("rating", 0)),
                    "address": details.get("formatted_address", place.get("formatted_address", "Address not available")),
                    "reviews": reviews,
                    "review_count": len(reviews),
                    "types": details.get("types", place.get("types", [])),
                    "location": location_coords
                }
                places.append(place_info)
            except Exception as e:
                place_info = {
                    "name": place.get("name", "Unknown"),
                    "rating": place.get("rating", 0),
                    "address": place.get("formatted_address", "Address not available"),
                    "reviews": [],
                    "review_count": 0,
                    "types": place.get("types", [])
                }
                places.append(place_info)
        
        result = {
            "query": query,
            "places": places,
            "count": len(places)
        }
        
        return result
    except Exception as e:
        error_result = {
            "error": f"Failed to search places: {str(e)}",
            "places": []
        }
        return error_result

