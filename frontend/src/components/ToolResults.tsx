import React from "react";

interface FlightResult {
  price: string;
  airline: string;
  departure_time: string;
  arrival_time: string;
  duration: string;
  stops: number;
}

interface PlaceResult {
  name: string;
  rating: number;
  address: string;
  reviews: Array<{
    author: string;
    rating: number;
    text: string;
  }>;
}

interface ToolResultsProps {
  flights?: {
    departure: string;
    arrival: string;
    date: string;
    flights: FlightResult[];
  };
  places?: {
    query: string;
    places: PlaceResult[];
  };
}

export function ToolResults({ flights, places }: ToolResultsProps) {
  if (!flights && !places) {
    return null;
  }

  return (
    <div className="space-y-4">
      {flights && flights.flights.length > 0 && (
        <div className="bg-card rounded-lg border border-border shadow-sm p-4">
          <h3 className="font-semibold mb-2">
            Flights: {flights.departure} → {flights.arrival}
          </h3>
          <div className="space-y-2">
            {flights.flights.map((flight, idx) => (
              <div key={idx} className="border border-border rounded-lg p-3 bg-muted/30">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium">{flight.airline}</div>
                    <div className="text-sm text-muted-foreground">
                      {flight.departure_time} → {flight.arrival_time}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Duration: {flight.duration} • {flight.stops} stop(s)
                    </div>
                  </div>
                  <div className="text-lg font-bold">{flight.price}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {places && places.places.length > 0 && (
        <div className="bg-card rounded-lg border border-border shadow-sm p-4">
          <h3 className="font-semibold mb-2">Places: {places.query}</h3>
          <div className="space-y-3">
            {places.places.map((place, idx) => (
              <div key={idx} className="border border-border rounded-lg p-3 bg-muted/30">
                <div className="font-medium">{place.name}</div>
                <div className="text-sm text-muted-foreground">{place.address}</div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-sm">⭐ {place.rating}</span>
                </div>
                {place.reviews.length > 0 && (
                  <div className="mt-2 text-sm">
                    <div className="font-medium mb-1">Reviews:</div>
                    {place.reviews.slice(0, 2).map((review, rIdx) => (
                      <div key={rIdx} className="text-muted-foreground mb-1">
                        "{review.text}"
                        <span className="text-xs ml-2">- {review.author}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

