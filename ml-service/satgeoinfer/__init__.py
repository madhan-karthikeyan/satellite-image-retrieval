"""SatGeoInfer - Satellite Image Geolocation Inference System."""

from .embedder import Embedder, create_embedder
from .retriever import Retriever, create_retriever
from .pipeline import SatGeoInfer, create_pipeline
from .clustering import cluster_coordinates, weighted_centroid
from .confidence import geographic_inference, compute_confidence_radius, classify_confidence
from .utils import get_scene_distribution, get_secondary_clusters, haversine_distance

__version__ = "1.0.0"

__all__ = [
    "Embedder",
    "create_embedder",
    "Retriever",
    "create_retriever",
    "SatGeoInfer",
    "create_pipeline",
    "cluster_coordinates",
    "weighted_centroid",
    "geographic_inference",
    "compute_confidence_radius",
    "classify_confidence",
    "get_scene_distribution",
    "get_secondary_clusters",
    "haversine_distance",
]
