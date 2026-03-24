import logging
from typing import Tuple, List
import numpy as np

logger = logging.getLogger(__name__)


def pixel_to_latlon(
    x: float,
    y: float,
    width: int,
    height: int,
    lat_top: float,
    lon_left: float,
    lat_bottom: float,
    lon_right: float
) -> Tuple[float, float]:
    """Convert pixel coordinates to geographic coordinates.
    
    Args:
        x: Pixel x coordinate (0 = left edge)
        y: Pixel y coordinate (0 = top edge)
        width: Image width in pixels
        height: Image height in pixels
        lat_top: Latitude of top edge
        lon_left: Longitude of left edge
        lat_bottom: Latitude of bottom edge
        lon_right: Longitude of right edge
        
    Returns:
        Tuple of (latitude, longitude)
    """
    # Clamp to image bounds
    x = max(0, min(x, width - 1))
    y = max(0, min(y, height - 1))
    
    # Convert pixel to relative position (0-1)
    rel_x = x / width if width > 0 else 0.5
    rel_y = y / height if height > 0 else 0.5
    
    # Convert to geographic coordinates
    lat = lat_top - (rel_y * (lat_top - lat_bottom))
    lon = lon_left + (rel_x * (lon_right - lon_left))
    
    return lat, lon


def bbox_to_latlon(
    bbox: Tuple[int, int, int, int],
    width: int,
    height: int,
    lat_top: float,
    lon_left: float,
    lat_bottom: float,
    lon_right: float
) -> dict:
    """Convert bounding box (pixel coords) to geographic coordinates.
    
    Args:
        bbox: (x_min, y_min, x_max, y_max) in pixels
        width: Image width
        height: Image height
        lat_top: Latitude of top edge
        lon_left: Longitude of left edge
        lat_bottom: Latitude of bottom edge
        lon_right: Longitude of right edge
        
    Returns:
        Dictionary with geographic bounds
    """
    x_min, y_min, x_max, y_max = bbox
    
    # Get corner coordinates
    lat_top_px, lon_left_px = pixel_to_latlon(
        x_min, y_min, width, height,
        lat_top, lon_left, lat_bottom, lon_right
    )
    lat_bottom_px, lon_right_px = pixel_to_latlon(
        x_max, y_max, width, height,
        lat_top, lon_left, lat_bottom, lon_right
    )
    
    # Calculate center
    lat_center = (lat_top_px + lat_bottom_px) / 2
    lon_center = (lon_left_px + lon_right_px) / 2
    
    return {
        "lat_top": lat_top_px,
        "lon_left": lon_left_px,
        "lat_bottom": lat_bottom_px,
        "lon_right": lon_right_px,
        "lat_center": lat_center,
        "lon_center": lon_center,
        "bbox_pixel": bbox
    }


def latlon_to_pixel(
    lat: float,
    lon: float,
    width: int,
    height: int,
    lat_top: float,
    lon_left: float,
    lat_bottom: float,
    lon_right: float
) -> Tuple[int, int]:
    """Convert geographic coordinates to pixel coordinates.
    
    Args:
        lat: Latitude
        lon: Longitude
        width: Image width in pixels
        height: Image height in pixels
        lat_top: Latitude of top edge
        lon_left: Longitude of left edge
        lat_bottom: Latitude of bottom edge
        lon_right: Longitude of right edge
        
    Returns:
        Tuple of (x, y) pixel coordinates
    """
    # Clamp to bounds
    lat = max(lat_bottom, min(lat, lat_top))
    lon = max(lon_left, min(lon, lon_right))
    
    # Calculate relative position
    rel_y = (lat_top - lat) / (lat_top - lat_bottom) if (lat_top - lat_bottom) != 0 else 0.5
    rel_x = (lon - lon_left) / (lon_right - lon_left) if (lon_right - lon_left) != 0 else 0.5
    
    # Convert to pixel coordinates
    x = int(rel_x * width)
    y = int(rel_y * height)
    
    return x, y


def get_dummy_geobounds(
    chip_id: str,
    seed: int = 0
) -> dict:
    """Generate dummy geographic bounds for testing/demo.
    
    Args:
        chip_id: Chip identifier for seeding
        seed: Random seed
        
    Returns:
        Dictionary with dummy geo bounds
    """
    np.random.seed(hash(chip_id) % 2**32 + seed)
    
    lat = np.random.uniform(-85, 85)
    lon = np.random.uniform(-180, 180)
    
    # Small region (1km x 1km approx)
    lat_range = 0.01
    lon_range = 0.01
    
    return {
        "lat_top": lat + lat_range / 2,
        "lat_bottom": lat - lat_range / 2,
        "lon_left": lon - lon_range / 2,
        "lon_right": lon + lon_range / 2
    }


def calculate_distance_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """Calculate distance between two coordinates in meters (Haversine).
    
    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate
        
    Returns:
        Distance in meters
    """
    from math import radians, cos, sin, asin, sqrt
    
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371000  # Radius of earth in meters
    return c * r


def validate_geobounds(bounds: dict) -> bool:
    """Validate geographic bounds dictionary.
    
    Args:
        bounds: Bounds dictionary with lat/lon keys
        
    Returns:
        True if valid
    """
    required_keys = {"lat_top", "lat_bottom", "lon_left", "lon_right"}
    if not all(k in bounds for k in required_keys):
        return False
    
    lat_top = bounds["lat_top"]
    lat_bottom = bounds["lat_bottom"]
    lon_left = bounds["lon_left"]
    lon_right = bounds["lon_right"]
    
    # Validate ranges
    if not (-90 <= lat_bottom <= lat_top <= 90):
        return False
    if not (-180 <= lon_left <= lon_right <= 180):
        return False
    
    return True
