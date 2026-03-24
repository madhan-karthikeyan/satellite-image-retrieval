export interface Coordinates {
  latitude: number;
  longitude: number;
  confidence?: number;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  imageId?: string;
}

export interface CoordinatesResponse {
  success: boolean;
  coordinates?: Coordinates;
  message?: string;
}

export interface ApiError {
  message: string;
  code?: string;
}
