"""Geographic clustering module with adaptive DBSCAN and outlier removal."""

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from haversine import haversine as haversine_calc
from typing import Optional, Tuple


def deg_to_rad(deg: float) -> float:
    """Convert degrees to radians."""
    return deg * np.pi / 180.0


def rad_to_deg(rad: float) -> float:
    """Convert radians to degrees."""
    return rad * 180.0 / np.pi


def weighted_centroid_3d(
    coords_rad: np.ndarray,
    weights: np.ndarray
) -> np.ndarray:
    """Compute weighted 3D Cartesian centroid (antimeridian-safe).
    
    Args:
        coords_rad: Array of (lat, lon) in radians, shape (n, 2)
        weights: Array of weights, shape (n,)
    
    Returns:
        Centroid coordinates in radians, shape (2,)
    """
    if len(coords_rad) == 0:
        return np.array([])
    
    weights = np.asarray(weights)
    if weights.sum() == 0:
        weights = np.ones_like(weights)
    weights = weights / weights.sum()
    
    lat_rad = coords_rad[:, 0]
    lon_rad = coords_rad[:, 1]
    
    x = np.cos(lat_rad) * np.cos(lon_rad)
    y = np.cos(lat_rad) * np.sin(lon_rad)
    z = np.sin(lat_rad)
    
    x_mean = np.sum(weights * x)
    y_mean = np.sum(weights * y)
    z_mean = np.sum(weights * z)
    
    lon_mean = np.arctan2(y_mean, x_mean)
    hyp = np.sqrt(x_mean**2 + y_mean**2)
    lat_mean = np.arctan2(z_mean, hyp)
    
    return np.array([lat_mean, lon_mean])


def compute_adaptive_epsilon(
    coords_rad: np.ndarray,
    k: int = 5,
    percentile: float = 95.0
) -> float:
    """Compute adaptive epsilon based on local density.
    
    Uses k-nearest neighbor distances to estimate local density
    and automatically determine appropriate epsilon.
    
    Args:
        coords_rad: Array of (lat, lon) in radians, shape (n, 2)
        k: Number of neighbors to consider
        percentile: Percentile of distances to use as epsilon
        
    Returns:
        Adaptive epsilon in radians
    """
    if len(coords_rad) < k + 1:
        return 500 / 6371.0
    
    nn = NearestNeighbors(metric='haversine', n_neighbors=min(k + 1, len(coords_rad)))
    nn.fit(coords_rad)
    distances, _ = nn.kneighbors(coords_rad)
    
    kth_distances = distances[:, k] if distances.shape[1] > k else distances[:, -1]
    epsilon = np.percentile(kth_distances, percentile)
    
    return float(epsilon)


def remove_outliers_by_distance(
    coords_rad: np.ndarray,
    weights: np.ndarray,
    max_distance_km: float = 1000.0
) -> Tuple[np.ndarray, np.ndarray]:
    """Remove outliers based on distance from weighted centroid.
    
    Args:
        coords_rad: Array of (lat, lon) in radians
        weights: Array of weights
        max_distance_km: Maximum allowed distance from centroid in km
        
    Returns:
        Tuple of (filtered_coords, filtered_weights)
    """
    if len(coords_rad) < 3:
        return coords_rad, weights
    
    centroid = weighted_centroid_3d(coords_rad, weights)
    
    centroid_lat = rad_to_deg(centroid[0])
    centroid_lon = rad_to_deg(centroid[1])
    
    distances = []
    for coord in coords_rad:
        lat = rad_to_deg(coord[0])
        lon = rad_to_deg(coord[1])
        dist = haversine_calc((centroid_lat, centroid_lon), (lat, lon))
        distances.append(dist)
    
    distances = np.array(distances)
    mask = distances <= max_distance_km
    
    return coords_rad[mask], weights[mask]


def iterative_outlier_removal(
    coords_rad: np.ndarray,
    weights: np.ndarray,
    threshold_km: float = 500.0,
    min_points: int = 3,
    max_iterations: int = 5
) -> Tuple[np.ndarray, np.ndarray]:
    """Iteratively remove outliers until convergence.
    
    Args:
        coords_rad: Array of (lat, lon) in radians
        weights: Array of weights
        threshold_km: Distance threshold for outlier removal
        min_points: Minimum number of points to keep
        max_iterations: Maximum iterations
        
    Returns:
        Tuple of (filtered_coords, filtered_weights)
    """
    current_coords = coords_rad.copy()
    current_weights = weights.copy()
    
    for _ in range(max_iterations):
        if len(current_coords) <= min_points:
            break
            
        centroid = weighted_centroid_3d(current_coords, current_weights)
        
        centroid_lat = rad_to_deg(centroid[0])
        centroid_lon = rad_to_deg(centroid[1])
        
        distances = []
        for coord in current_coords:
            lat = rad_to_deg(coord[0])
            lon = rad_to_deg(coord[1])
            dist = haversine_calc((centroid_lat, centroid_lon), (lat, lon))
            distances.append(dist)
        
        distances = np.array(distances)
        
        if np.all(distances <= threshold_km):
            break
            
        mask = distances <= threshold_km
        current_coords = current_coords[mask]
        current_weights = current_weights[mask]
    
    return current_coords, current_weights


def cluster_coordinates(
    candidates: list[dict],
    use_adaptive_eps: bool = True,
    base_eps_km: float = 500.0,
    min_samples: int = 2
) -> tuple:
    """Cluster coordinates using adaptive DBSCAN.
    
    Args:
        candidates: List of candidate dicts with lat, lon, similarity
        use_adaptive_eps: Use adaptive epsilon based on local density
        base_eps_km: Base epsilon in km (used if adaptive is disabled)
        min_samples: Minimum samples for DBSCAN
        
    Returns:
        Tuple of (dominant_coords_rad, dominant_weights, all_labels, all_coords_rad)
    """
    if len(candidates) < 2:
        return None
    
    lats = np.array([c["lat"] for c in candidates])
    lons = np.array([c["lon"] for c in candidates])
    similarities = np.array([c["similarity"] for c in candidates])
    
    coords_rad = np.column_stack([
        deg_to_rad(lats),
        deg_to_rad(lons)
    ])
    
    weights = similarities ** 2
    
    if use_adaptive_eps:
        eps_rad = compute_adaptive_epsilon(coords_rad, k=min(min_samples, len(candidates)-1))
        eps_rad = max(eps_rad, base_eps_km / 6371.0)
    else:
        eps_rad = base_eps_km / 6371.0
    
    clustering = DBSCAN(eps=eps_rad, min_samples=min_samples, metric='haversine')
    labels = clustering.fit_predict(coords_rad)
    
    unique_labels = set(labels)
    if len(unique_labels) <= 1 or (len(unique_labels) == 2 and -1 in labels):
        dominant_indices = np.arange(len(candidates))
    else:
        label_counts = {lab: np.sum(labels == lab) for lab in unique_labels if lab != -1}
        if not label_counts:
            dominant_indices = np.arange(len(candidates))
        else:
            dominant_label = max(label_counts, key=label_counts.get)
            dominant_indices = np.where(labels == dominant_label)[0]
    
    dominant_coords_rad = coords_rad[dominant_indices]
    dominant_weights = weights[dominant_indices]
    
    dominant_coords_rad, dominant_weights = iterative_outlier_removal(
        dominant_coords_rad,
        dominant_weights,
        threshold_km=400.0,
        min_points=3
    )
    
    return (dominant_coords_rad, dominant_weights, labels, coords_rad)


def weighted_centroid(coords: list[tuple], weights: list[float]) -> tuple:
    """Compute weighted centroid from coordinates and weights."""
    if not coords:
        return (0.0, 0.0)
    
    coords_rad = np.array([[deg_to_rad(lat), deg_to_rad(lon)] for lat, lon in coords])
    weights_arr = np.array(weights)
    
    centroid_rad = weighted_centroid_3d(coords_rad, weights_arr)
    
    if len(centroid_rad) == 0:
        return (0.0, 0.0)
    
    return (rad_to_deg(centroid_rad[0]), rad_to_deg(centroid_rad[1]))


def compute_cluster_statistics(
    coords_rad: np.ndarray,
    weights: np.ndarray,
    centroid_rad: np.ndarray
) -> dict:
    """Compute comprehensive statistics for a cluster.
    
    Args:
        coords_rad: Cluster coordinates in radians
        weights: Cluster weights
        centroid_rad: Centroid in radians
        
    Returns:
        Dictionary of cluster statistics
    """
    if len(coords_rad) == 0:
        return {}
    
    centroid_lat = rad_to_deg(centroid_rad[0])
    centroid_lon = rad_to_deg(centroid_rad[1])
    
    distances = []
    for coord in coords_rad:
        lat = rad_to_deg(coord[0])
        lon = rad_to_deg(coord[1])
        dist = haversine_calc((centroid_lat, centroid_lon), (lat, lon))
        distances.append(dist)
    
    distances = np.array(distances)
    weights_norm = weights / weights.sum()
    
    return {
        "mean_distance": float(np.mean(distances)),
        "std_distance": float(np.std(distances)),
        "median_distance": float(np.median(distances)),
        "max_distance": float(np.max(distances)),
        "weighted_mean_distance": float(np.sum(weights_norm * distances)),
        "compactness_score": float(1.0 / (1.0 + np.mean(distances))),
    }
