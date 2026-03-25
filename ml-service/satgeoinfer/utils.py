"""Utility functions for satellite geolocation inference."""

from collections import Counter
from functools import lru_cache
from haversine import haversine as haversine_calc
import numpy as np
import os


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate haversine distance between two points in km."""
    return haversine_calc((lat1, lon1), (lat2, lon2))


@lru_cache(maxsize=1000)
def reverse_geocode(lat: float, lon: float) -> dict:
    """Get location info from coordinates using reverse geocoding.
    
    Returns cached results to minimize API calls. Uses offline fallback
    with continent estimation when geocoding service unavailable.
    """
    try:
        from geopy.geocoders import Nominatim
        from geopy.extra.rate_limiter import RateLimiter
        
        geolocator = Nominatim(user_agent="satgeoinfer/geolocation")
        reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)
        location = reverse(f"{lat}, {lon}", language="en", timeout=5)
        
        if location and location.raw.get("address"):
            addr = location.raw["address"]
            return {
                "country": addr.get("country", ""),
                "country_code": addr.get("country_code", "").upper(),
                "region": addr.get("state", addr.get("region", "")),
                "city": addr.get("city", addr.get("town", addr.get("village", ""))),
                "continent": _get_continent_from_code(addr.get("country_code", "")),
            }
    except Exception:
        pass
    
    return {
        "country": "",
        "country_code": "",
        "region": "",
        "city": "",
        "continent": _estimate_continent(lat, lon)
    }


def _estimate_continent(lat: float, lon: float) -> str:
    """Estimate continent from coordinates as fallback."""
    if 35 <= lat <= 72 and -10 <= lon <= 40:
        return "Europe"
    elif -55 <= lat <= 60 and -130 <= lon <= -35:
        return "North America"
    elif -55 <= lat <= 15 and -80 <= lon <= -35:
        return "South America"
    elif -35 <= lat <= 35 and -20 <= lon <= 55:
        return "Africa"
    elif 10 <= lat <= 55 and 60 <= lon <= 150:
        return "Asia"
    elif -50 <= lat <= -10 and 110 <= lon <= 180:
        return "Oceania"
    return "Unknown"


def _get_continent_from_code(code: str) -> str:
    """Map country code to continent."""
    eu_codes = {"GB", "FR", "DE", "IT", "ES", "NL", "BE", "PT", "PL", "GR", "CZ", "AT", "CH", "SE", "NO", "FI", "DK", "IE", "RU", "UA", "TR"}
    na_codes = {"US", "CA", "MX"}
    sa_codes = {"BR", "AR", "CL", "CO", "PE", "VE"}
    af_codes = {"ZA", "EG", "NG", "KE", "MA", "GH", "ET"}
    as_codes = {"CN", "IN", "JP", "KR", "TH", "VN", "ID", "MY", "PH", "SG", "AE", "SA", "IL", "PK"}
    oc_codes = {"AU", "NZ"}
    
    code = code.upper()
    if code in eu_codes: return "Europe"
    if code in na_codes: return "North America"
    if code in sa_codes: return "South America"
    if code in af_codes: return "Africa"
    if code in as_codes: return "Asia"
    if code in oc_codes: return "Oceania"
    return "Unknown"


def get_country_distribution(candidates: list[dict]) -> dict[str, int]:
    """Get distribution of countries in candidates."""
    countries = []
    for c in candidates:
        lat, lon = c.get("lat", 0), c.get("lon", 0)
        geo_info = reverse_geocode(lat, lon)
        if geo_info.get("country"):
            countries.append(geo_info["country"])
    
    counter = Counter(countries)
    return dict(counter)


def get_scene_distribution(candidates: list[dict], labels: np.ndarray) -> dict[str, int]:
    """Get distribution of scene categories in candidates."""
    scene_labels = [c.get("scene_label", "unknown") for c in candidates]
    counter = Counter(scene_labels)
    return dict(counter)


def get_secondary_clusters(labels: np.ndarray, coords_rad: np.ndarray) -> list[dict]:
    """Get information about secondary clusters (excluding dominant)."""
    from .clustering import weighted_centroid_3d, rad_to_deg, deg_to_rad

    unique_labels = set(labels)
    if len(unique_labels) <= 1:
        return []

    clusters = []
    for label in unique_labels:
        if label == -1:
            continue
        
        indices = np.where(labels == label)[0]
        if len(indices) < 2:
            continue

        cluster_coords = coords_rad[indices]
        
        weights = np.ones(len(indices))
        centroid_rad = weighted_centroid_3d(cluster_coords, weights)

        if len(centroid_rad) > 0:
            clusters.append({
                "centroid_lat": rad_to_deg(centroid_rad[0]),
                "centroid_lon": rad_to_deg(centroid_rad[1]),
                "size": len(indices)
            })

    clusters.sort(key=lambda x: x["size"], reverse=True)
    return clusters[1:6]


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude values."""
    return -90 <= lat <= 90 and -180 <= lon <= 180
