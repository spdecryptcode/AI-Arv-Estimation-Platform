"""Data transformation utilities for normalizing and enriching records."""
from typing import Dict, Any, List


class AddressNormalizer:
    @staticmethod
    def normalize(record: Dict[str, Any]) -> Dict[str, Any]:
        """Lowercase string values and strip whitespace from all fields."""
        normalized: Dict[str, Any] = {}
        for k, v in record.items():
            if isinstance(v, str):
                normalized[k.lower()] = v.strip()
            else:
                normalized[k.lower()] = v
        return normalized


class Geocoder:
    @staticmethod
    def geocode(address: str) -> Dict[str, Any]:
        """Return dummy lat/lon for the given address.

        A real implementation would call an external geocoding API such as
        Nominatim, Google, or Mapbox and return coordinates plus a confidence
        score.
        """
        return {"lat": 0.0, "lon": 0.0, "confidence": 1.0}


class PropertyNormalizer:
    @staticmethod
    def normalize(record: Dict[str, Any]) -> Dict[str, Any]:
        """Map variant field names into a canonical schema."""
        mapping = {
            "addr": "address",
            "zip_code": "zip",
            "ownername": "owner",
        }
        result: Dict[str, Any] = {}
        for k, v in record.items():
            key = mapping.get(k, k)
            result[key] = v
        return result


class GeoEnricher:
    @staticmethod
    def enrich(record: Dict[str, Any]) -> Dict[str, Any]:
        # placeholder; could add neighborhood, flood zone etc.
        record["neighborhood"] = "unknown"
        return record


class AmenityScorer:
    @staticmethod
    def score(record: Dict[str, Any]) -> float:
        """Compute a simple score based on number of amenities listed."""
        amenities = record.get("amenities")
        if isinstance(amenities, list):
            return float(len(amenities))
        return 0.0
