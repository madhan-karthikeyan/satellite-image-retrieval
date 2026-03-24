import axios, { AxiosError } from 'axios';
import type { UploadResponse, CoordinatesResponse, ApiError } from '../types';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const errorMessage = error.response?.data?.message || error.message || 'An unexpected error occurred';
    return Promise.reject(new Error(errorMessage));
  }
);

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

export const getCoordinates = async (imageId: string): Promise<CoordinatesResponse> => {
  const response = await apiClient.get<CoordinatesResponse>(`/get-coordinates?imageId=${imageId}`);
  return response.data;
};

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
