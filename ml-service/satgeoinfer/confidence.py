"""Confidence estimation with calibrated scoring for geographic inference."""

from typing import Optional
import numpy as np
from haversine import haversine


def compute_confidence_radius(
    coords_rad: np.ndarray,
    centroid_rad: np.ndarray,
    percentile: float = 90.0
) -> float:
    """Compute confidence radius as percentile distance from centroid.
    
    Args:
        coords_rad: Array of coordinates in radians
        centroid_rad: Centroid in radians
        percentile: Percentile to use for radius
        
    Returns:
        Confidence radius in km
    """
    if len(coords_rad) == 0:
        return float("inf")

    centroid_lat = centroid_rad[0] * (180.0 / np.pi)
    centroid_lon = centroid_rad[1] * (180.0 / np.pi)
    centroid_deg = (centroid_lat, centroid_lon)

    distances = []
    for coord_rad in coords_rad:
        lat = coord_rad[0] * (180.0 / np.pi)
        lon = coord_rad[1] * (180.0 / np.pi)
        dist = haversine(centroid_deg, (lat, lon))
        distances.append(dist)

    if len(distances) > 0:
        radius = np.percentile(distances, percentile)
    else:
        radius = float("inf")

    return float(radius)


def compute_similarity_stats(weights: np.ndarray) -> dict:
    """Compute comprehensive statistics about similarity scores."""
    if len(weights) == 0:
        return {
            "mean": 0.0, "min": 0.0, "max": 0.0,
            "std": 0.0, "q25": 0.0, "q75": 0.0,
            "skewness": 0.0, "kurtosis": 0.0
        }

    return {
        "mean": float(np.mean(weights)),
        "min": float(np.min(weights)),
        "max": float(np.max(weights)),
        "std": float(np.std(weights)),
        "q25": float(np.percentile(weights, 25)),
        "q75": float(np.percentile(weights, 75)),
        "skewness": float(_compute_skewness(weights)),
        "kurtosis": float(_compute_kurtosis(weights)),
    }


def _compute_skewness(data: np.ndarray) -> float:
    """Compute skewness of distribution."""
    if len(data) < 3:
        return 0.0
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return 0.0
    return np.mean(((data - mean) / std) ** 3)


def _compute_kurtosis(data: np.ndarray) -> float:
    """Compute kurtosis of distribution."""
    if len(data) < 4:
        return 0.0
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return 0.0
    return np.mean(((data - mean) / std) ** 4) - 3.0


def compute_calibrated_confidence_score(
    radius: float,
    cluster_size: int,
    similarity_stats: dict,
    total_candidates: int
) -> float:
    """Compute a calibrated confidence score between 0 and 1.
    
    This function combines multiple factors into a single calibrated score:
    - Radius score: smaller radius = higher score
    - Size score: larger cluster = higher score  
    - Similarity score: higher similarity = higher score
    - Diversity score: more candidates = slightly higher score
    
    Args:
        radius: Confidence radius in km
        cluster_size: Number of images in dominant cluster
        similarity_stats: Dictionary of similarity statistics
        total_candidates: Total number of candidates retrieved
        
    Returns:
        Calibrated confidence score between 0 and 1
    """
    radius_score = np.exp(-radius / 500.0)
    
    size_score = min(cluster_size / 20.0, 1.0)
    
    mean_sim = similarity_stats.get("mean", 0.0)
    q25_sim = similarity_stats.get("q25", 0.0)
    similarity_score = (mean_sim * 0.6 + q25_sim * 0.4)
    
    diversity_score = min(total_candidates / 100.0, 1.0) * 0.1
    
    weights = {
        "radius": 0.35,
        "size": 0.30,
        "similarity": 0.30,
        "diversity": 0.05
    }
    
    final_score = (
        weights["radius"] * radius_score +
        weights["size"] * size_score +
        weights["similarity"] * similarity_score +
        weights["diversity"] * diversity_score
    )
    
    return float(np.clip(final_score, 0.0, 1.0))


def classify_confidence(
    radius: float,
    cluster_size: int,
    similarity_stats: Optional[dict] = None,
    calibrated_score: Optional[float] = None
) -> str:
    """Classify confidence level with calibrated scoring.
    
    Uses both rule-based and calibrated score for robust classification.
    
    Args:
        radius: Confidence radius in km
        cluster_size: Number of images in dominant cluster
        similarity_stats: Dictionary of similarity statistics
        calibrated_score: Pre-computed calibrated confidence score
        
    Returns:
        Confidence level: 'high', 'medium', or 'low'
    """
    if similarity_stats is None:
        similarity_stats = {}

    mean_sim = similarity_stats.get("mean", 0.0)
    min_sim = similarity_stats.get("min", 0.0)
    q25_sim = similarity_stats.get("q25", 0.0)
    q75_sim = similarity_stats.get("q75", 0.0)

    if calibrated_score is not None:
        if calibrated_score >= 0.70:
            return "high"
        elif calibrated_score >= 0.45:
            return "medium"
        else:
            return "low"

    high_conditions = (
        radius <= 150 and
        cluster_size >= 8 and
        mean_sim >= 0.65 and
        min_sim >= 0.50
    )

    if high_conditions:
        return "high"

    medium_conditions = (
        radius <= 400 and
        cluster_size >= 4 and
        (mean_sim >= 0.55 or q25_sim >= 0.45)
    )

    if medium_conditions:
        return "medium"

    return "low"


def geographic_inference(candidates: list[dict]) -> Optional[dict]:
    """Perform complete geographic inference from candidates with improved accuracy."""
    from .clustering import (
        cluster_coordinates,
        weighted_centroid_3d,
        rad_to_deg,
        compute_cluster_statistics
    )

    if len(candidates) < 2:
        return None

    cluster_result = cluster_coordinates(
        candidates,
        use_adaptive_eps=True,
        base_eps_km=500.0,
        min_samples=2
    )
    
    if cluster_result is None:
        return None

    dominant_coords_rad, dominant_weights, all_labels, all_coords_rad = cluster_result

    if len(dominant_coords_rad) == 0:
        return None

    centroid_rad = weighted_centroid_3d(dominant_coords_rad, dominant_weights)
    if len(centroid_rad) == 0:
        return None

    centroid_lat = rad_to_deg(centroid_rad[0])
    centroid_lon = rad_to_deg(centroid_rad[1])

    radius = compute_confidence_radius(dominant_coords_rad, centroid_rad)

    similarity_stats = compute_similarity_stats(dominant_weights)
    
    calibrated_score = compute_calibrated_confidence_score(
        radius=radius,
        cluster_size=len(dominant_coords_rad),
        similarity_stats=similarity_stats,
        total_candidates=len(candidates)
    )
    
    confidence = classify_confidence(
        radius,
        len(dominant_coords_rad),
        similarity_stats,
        calibrated_score
    )
    
    cluster_stats = compute_cluster_statistics(
        dominant_coords_rad,
        dominant_weights,
        centroid_rad
    )

    from .utils import get_scene_distribution, get_secondary_clusters, reverse_geocode
    scene_dist = get_scene_distribution(candidates, all_labels)
    secondary_clusters = get_secondary_clusters(all_labels, all_coords_rad)
    
    geo_info = reverse_geocode(float(centroid_lat), float(centroid_lon))

    return {
        "centroid_lat": float(centroid_lat),
        "centroid_lon": float(centroid_lon),
        "confidence_radius_km": float(radius),
        "confidence_level": confidence,
        "confidence_score": calibrated_score,
        "cluster_size": int(len(dominant_coords_rad)),
        "total_candidates": int(len(candidates)),
        "scene_distribution": scene_dist,
        "secondary_clusters": secondary_clusters,
        "similarity_stats": similarity_stats,
        "cluster_stats": cluster_stats,
        "country": geo_info.get("country", ""),
        "country_code": geo_info.get("country_code", ""),
        "region": geo_info.get("region", ""),
        "city": geo_info.get("city", ""),
        "continent": geo_info.get("continent", ""),
    }
