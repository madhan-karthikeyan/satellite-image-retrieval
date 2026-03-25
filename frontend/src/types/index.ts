export interface Coordinates {
  latitude: number;
  longitude: number;
  confidence?: number;
  confidenceLevel?: string;
  radiusKm?: number;
  clusterSize?: number;
  totalCandidates?: number;
  sceneDistribution?: Record<string, number>;
  explanation?: string;
}

export interface CoordinatesResponse {
  success: boolean;
  coordinates?: Coordinates;
  message?: string;
  candidatesRetrieved?: number;
}

export interface InferResponse {
  status: string;
  centroid_lat?: number;
  centroid_lon?: number;
  confidence_radius_km?: number;
  confidence_level?: string;
  cluster_size?: number;
  total_candidates?: number;
  scene_distribution?: Record<string, number>;
  secondary_clusters?: SecondaryCluster[];
  similarity_stats?: SimilarityStats;
  explanation?: string;
  message?: string;
  candidates_retrieved?: number;
}

export interface SecondaryCluster {
  centroid_lat: number;
  centroid_lon: number;
  size: number;
}

export interface SimilarityStats {
  mean: number;
  min: number;
  max: number;
  std: number;
  q25: number;
  q75: number;
}

export interface ApiError {
  message: string;
  code?: string;
}
