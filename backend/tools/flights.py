"""Flight prices tool using SerpAPI."""

import os
import json
import requests
from typing import Dict, List, Optional
from tools.airport_codes import CITY_TO_AIRPORT

def get_airport_code(location: str) -> str:
    """
    Convert city name to IATA airport code.
    
    Args:
        location: City name or airport code
        
    Returns:
        IATA airport code (3-letter code)
    """
    location_lower = location.lower().strip()
    
    if location_lower in CITY_TO_AIRPORT:
        airport_code = CITY_TO_AIRPORT[location_lower]
        return airport_code
    
    if len(location) == 3 and location.isupper():
        return location
    
    for city, code in CITY_TO_AIRPORT.items():
        if city in location_lower or location_lower in city:
            return code
    
    return location


def get_flight_prices(
    departure: str,
    arrival: str,
    date: str,
    return_date: Optional[str] = None,
    flight_type: Optional[str] = None,
    currency: str = "USD"
) -> Dict:
    """
    Get flight prices from SerpAPI Google Flights.
    
    CRITICAL VALIDATION REQUIREMENT:
    The departure parameter MUST be explicitly stated by the user in the conversation.
    The agent calling this function MUST verify the user explicitly stated their departure city
    before calling this function. If departure city is not explicitly stated, the agent MUST
    ask the user "Where are you departing from?" first.
    
    REQUIRED PARAMETERS: departure, arrival, and date must all be provided.
    SerpAPI requires outbound_date for all flight searches.
    
    Args:
        departure: Departure city/airport code (e.g., "New York", "JFK", "ATL")
                   MUST be explicitly stated by user - never inferred or assumed
        arrival: Arrival city/airport code (e.g., "NRT", "Tokyo", "Japan")
        date: Departure date in YYYY-MM-DD format (REQUIRED)
        return_date: Return date in YYYY-MM-DD format (optional, for round trips)
        flight_type: "one-way" or "round-trip" (optional, auto-detected if not provided)
        currency: Currency code (default: USD)
    
    Returns:
        Dictionary with flight information including prices, durations, airlines
    """
    
    if not date:
        error_result = {
            "error": "Date parameter is required. SerpAPI requires outbound_date for all flight searches.",
            "flights": []
        }
        return error_result
    
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        error_result = {
            "error": "SERPAPI_API_KEY not configured",
            "flights": []
        }
        return error_result
    
    departure_code = get_airport_code(departure)
    arrival_code = get_airport_code(arrival)
    
    if return_date:
        flight_type = "round-trip"
    elif flight_type is None:
        flight_type = "one-way"
    
    url = "https://serpapi.com/search"
    
    params = {
        "engine": "google_flights",
        "api_key": api_key,
        "departure_id": departure_code,
        "arrival_id": arrival_code,
        "currency": currency,
    }
    
    if flight_type == "round-trip":
        params["type"] = 1
        params["outbound_date"] = date
        if return_date:
            params["return_date"] = return_date
    else:
        params["type"] = 2
        params["outbound_date"] = date
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        response.raise_for_status()
        data = response.json()
        
        flights = []
        flight_options = []
        
        if "best_flights" in data and data["best_flights"]:
            flight_options.extend(data["best_flights"])
        
        if "other_flights" in data and data["other_flights"]:
            flight_options.extend(data["other_flights"])
        
        if not flight_options and "flights" in data and data["flights"]:
            flight_options = data["flights"]
        
        for option in flight_options[:5]:
            price = option.get("price")
            total_duration_minutes = option.get("total_duration", 0)
            layovers = option.get("layovers", [])
            option_type = option.get("type", "Unknown")
            
            flight_legs = option.get("flights", [])
            if not flight_legs:
                continue
            
            first_leg = flight_legs[0]
            departure_airport = first_leg.get("departure_airport", {})
            departure_time = departure_airport.get("time", "N/A")
            departure_airport_name = departure_airport.get("name", "N/A")
            departure_airport_id = departure_airport.get("id", "N/A")
            
            last_leg = flight_legs[-1]
            arrival_airport = last_leg.get("arrival_airport", {})
            arrival_time = arrival_airport.get("time", "N/A")
            arrival_airport_name = arrival_airport.get("name", "N/A")
            arrival_airport_id = arrival_airport.get("id", "N/A")
            
            airlines = []
            for leg in flight_legs:
                airline = leg.get("airline", "")
                if airline and airline not in airlines:
                    airlines.append(airline)
            
            num_stops = len(layovers)
            
            if total_duration_minutes:
                hours = total_duration_minutes // 60
                minutes = total_duration_minutes % 60
                if hours > 0 and minutes > 0:
                    duration_str = f"{hours}h {minutes}m"
                elif hours > 0:
                    duration_str = f"{hours}h"
                else:
                    duration_str = f"{minutes}m"
            else:
                duration_str = "N/A"
            
            layover_info = []
            for layover in layovers:
                layover_name = layover.get("name", "Unknown")
                layover_duration = layover.get("duration", 0)
                overnight = layover.get("overnight", False)
                
                if layover_duration:
                    layover_hours = layover_duration // 60
                    layover_mins = layover_duration % 60
                    if layover_hours > 0 and layover_mins > 0:
                        layover_duration_str = f"{layover_hours}h {layover_mins}m"
                    elif layover_hours > 0:
                        layover_duration_str = f"{layover_hours}h"
                    else:
                        layover_duration_str = f"{layover_mins}m"
                else:
                    layover_duration_str = "N/A"
                
                layover_desc = f"{layover_name} ({layover_duration_str})"
                if overnight:
                    layover_desc += " [overnight]"
                layover_info.append(layover_desc)
            
            flight_info = {
                "price": price,
                "total_duration": duration_str,
                "total_duration_minutes": total_duration_minutes,
                "departure_time": departure_time,
                "departure_airport": departure_airport_name,
                "departure_airport_id": departure_airport_id,
                "arrival_time": arrival_time,
                "arrival_airport": arrival_airport_name,
                "arrival_airport_id": arrival_airport_id,
                "airlines": airlines,
                "airline": ", ".join(airlines) if airlines else "Unknown",
                "stops": num_stops,
                "layovers": layover_info,
                "type": option_type,
                "num_legs": len(flight_legs)
            }
            flights.append(flight_info)
        
        prices = [f["price"] for f in flights if f.get("price") and isinstance(f.get("price"), (int, float))]
        summary = {}
        if prices:
            summary["cheapest_price"] = min(prices)
            summary["most_expensive_price"] = max(prices)
            summary["average_price"] = sum(prices) / len(prices)
            summary["price_range"] = f"${min(prices):.0f} - ${max(prices):.0f}"
        
        result = {
            "departure": departure,
            "arrival": arrival,
            "date": date,
            "return_date": return_date,
            "flight_type": flight_type,
            "flights": flights,
            "count": len(flights),
            "summary": summary
        }
        
        return result
    except requests.exceptions.RequestException as e:
        error_details = str(e)
        
        error_result = {
            "error": f"Failed to fetch flight data: {error_details}",
            "flights": []
        }
        return error_result
    except Exception as e:
        error_result = {
            "error": f"Unexpected error: {str(e)}",
            "flights": []
        }
        return error_result

