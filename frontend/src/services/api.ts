/**
 * API Service for Satellite Intelligence System
 * 
 * This module handles all HTTP requests to the backend FastAPI server.
 */

import axios, { AxiosError } from 'axios';
import type { InferResponse, CoordinatesResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const message = (error.response?.data as any)?.detail || error.message || 'An unexpected error occurred';
    return Promise.reject(new Error(message));
  }
);

export const inferLocation = async (file: File): Promise<CoordinatesResponse> => {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('explain', 'false');
  formData.append('second_stage', 'false');

  try {
    const response = await apiClient.post<InferResponse>('/infer', formData);
    const data = response.data;
    
    if (data.status === 'success') {
      const confidence = calculateConfidence(data.confidence_level || 'medium', data.confidence_radius_km || 1000);
      return {
        success: true,
        coordinates: {
          latitude: data.centroid_lat || 0,
          longitude: data.centroid_lon || 0,
          confidence: confidence,
          confidenceLevel: data.confidence_level,
          radiusKm: data.confidence_radius_km,
          clusterSize: data.cluster_size,
          totalCandidates: data.total_candidates,
          sceneDistribution: data.scene_distribution,
          explanation: data.explanation
        }
      };
    } else if (data.status === 'insufficient_confidence') {
      return {
        success: false,
        message: data.message || 'Insufficient confidence',
        candidatesRetrieved: data.candidates_retrieved
      };
    }
    
    return {
      success: false,
      message: 'Unknown response status'
    };
  } catch (error) {
    if (error instanceof Error) {
      return {
        success: false,
        message: error.message
      };
    }
    return {
      success: false,
      message: 'An unexpected error occurred'
    };
  }
};

function calculateConfidence(level: string, radiusKm: number): number {
  switch (level) {
    case 'high':
      return Math.max(0.8, 1 - (radiusKm / 2000));
    case 'medium':
      return Math.max(0.5, 0.8 - (radiusKm / 3000));
    case 'low':
      return Math.max(0.2, 0.5 - (radiusKm / 5000));
    default:
      return 0.5;
  }
}

export const getHealthStatus = async (): Promise<{ healthy: boolean; indexSize: number }> => {
  try {
    const response = await apiClient.get('/health');
    return {
      healthy: response.data.status === 'healthy',
      indexSize: response.data.index_size || 0
    };
  } catch {
    return {
      healthy: false,
      indexSize: 0
    };
  }
};

export const getIndexStats = async (): Promise<{ collectionSize: number; collectionName: string } | null> => {
  try {
    const response = await apiClient.get('/index/stats');
    return {
      collectionSize: response.data.collection_size,
      collectionName: response.data.collection_name
    };
  } catch {
    return null;
  }
};
