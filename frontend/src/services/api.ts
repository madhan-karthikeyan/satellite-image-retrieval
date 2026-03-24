/**
 * API Service for Satellite Intelligence System
 * 
 * This module handles all HTTP requests to the backend FastAPI server.
 * Base URL points to the ml-service running on localhost:8000
 */

import axios, { AxiosError } from 'axios';
import type { UploadResponse, CoordinatesResponse, ApiError } from '../types';

/**
 * FastAPI backend server URL
 * TODO: Update this to production URL when deploying
 */
const API_BASE_URL = 'http://localhost:8000';

/**
 * Axios instance with default configuration
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Response interceptor for error handling
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const errorMessage = error.response?.data?.message || error.message || 'An unexpected error occurred';
    return Promise.reject(new Error(errorMessage));
  }
);

/**
 * Upload an image file to the server
 * 
 * Endpoint: POST /upload-image
 * 
 * @param file - The image file to upload
 * @returns UploadResponse with success status and image_id
 * 
 * Response Format:
 * {
 *   "success": true,
 *   "message": "Image uploaded successfully",
 *   "image_id": "uuid-string"
 * }
 */
export const uploadImage = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('image', file);

  const response = await apiClient.post<UploadResponse>('/upload-image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Get extracted coordinates for an uploaded image
 * 
 * Endpoint: GET /get-coordinates
 * 
 * @param imageId - The image ID returned from upload endpoint
 * @returns CoordinatesResponse with latitude, longitude, and confidence
 * 
 * Response Format:
 * {
 *   "success": true,
 *   "coordinates": {
 *     "latitude": 13.0827,
 *     "longitude": 80.2707,
 *     "confidence": 0.92
 *   }
 * }
 */
export const getCoordinates = async (imageId: string): Promise<CoordinatesResponse> => {
  const response = await apiClient.get<CoordinatesResponse>(`/get-coordinates?image_id=${imageId}`);
  return response.data;
};

/**
 * Convenience function to upload image and get coordinates in one call
 * 
 * @param file - The image file to process
 * @returns CoordinatesResponse with extracted coordinates
 */
export const uploadImageAndGetCoordinates = async (file: File): Promise<CoordinatesResponse> => {
  const uploadResponse = await uploadImage(file);
  
  if (!uploadResponse.success || !uploadResponse.imageId) {
    return {
      success: false,
      message: uploadResponse.message || 'Failed to upload image',
    };
  }

  return getCoordinates(uploadResponse.imageId);
};
