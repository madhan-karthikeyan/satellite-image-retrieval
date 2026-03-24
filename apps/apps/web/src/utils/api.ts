const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

export interface HealthResponse {
  status: string;
  embedding_model: string;
  chroma_available: boolean;
  device: string;
}

export interface ChipInfo {
  id: string;
  filename: string;
  object_name: string;
  width: number;
  height: number;
  channels: number;
  uploaded_at: string;
}

export interface ChipUploadResponse {
  success: boolean;
  message: string;
  chip_id: string;
  chip_info: ChipInfo;
}

export interface ImageryInfo {
  filename: string;
  width: number;
  height: number;
  bands: number;
  format: string;
}

export interface ImageryListResponse {
  success: boolean;
  imagery_count: number;
  imagery_list: ImageryInfo[];
}

export interface SearchResult {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
  searched_object_name: string;
  target_imagery_file_name: string;
  similarity_score: number;
}

export interface SearchRequest {
  object_name: string;
  target_directory: string;
  output_directory: string;
  similarity_threshold: number;
  batch_name?: string;
}

export interface SearchResponse {
  success: boolean;
  message: string;
  results_count: number;
  results: SearchResult[];
  output_file: string | null;
  processing_time_seconds: number;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        ...options.headers,
      },
    };

    if (!(options.body instanceof FormData)) {
      config.headers = {
        "Content-Type": "application/json",
        ...config.headers,
      };
    }

    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>("/health");
  }

  async uploadChip(file: File, objectName: string): Promise<ChipUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("object_name", objectName);

    const response = await fetch(`${this.baseUrl}/upload/chip`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Upload failed");
    }
    return data;
  }

  async uploadChipFromBox(
    file: File,
    objectName: string,
    bbox: { x_min: number; y_min: number; x_max: number; y_max: number }
  ): Promise<{ success: boolean; message: string; chip_id: string; bbox: typeof bbox }> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("object_name", objectName);
    formData.append("x_min", bbox.x_min.toString());
    formData.append("y_min", bbox.y_min.toString());
    formData.append("x_max", bbox.x_max.toString());
    formData.append("y_max", bbox.y_max.toString());

    const response = await fetch(`${this.baseUrl}/upload/chip-from-box`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Upload failed");
    }
    return data;
  }

  async listImagery(directory: string): Promise<ImageryListResponse> {
    return this.request<ImageryListResponse>(
      `/imagery/list?directory=${encodeURIComponent(directory)}`
    );
  }

  async getImageryPreview(
    filename: string,
    directory: string
  ): Promise<string> {
    const params = new URLSearchParams({
      directory,
      filename,
    });
    return `${this.baseUrl}/imagery/preview?${params}`;
  }

  getTileUrl(
    filename: string,
    directory: string,
    x: number,
    y: number,
    size: number = 256
  ): string {
    const params = new URLSearchParams({
      directory,
      filename,
      x: x.toString(),
      y: y.toString(),
      size: size.toString(),
    });
    return `${this.baseUrl}/imagery/tile?${params}`;
  }

  async executeSearch(request: SearchRequest): Promise<SearchResponse> {
    return this.request<SearchResponse>("/search/execute", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async getSearchStatus(): Promise<{
    status: string;
    available_objects: string[];
    total_chips: number;
    search_threshold: number;
  }> {
    return this.request("/search/status");
  }

  async listChips(): Promise<{
    success: boolean;
    total_chips: number;
    chips: { object_name: string; count: number }[];
  }> {
    return this.request("/upload/chips");
  }

  async deleteChips(objectName: string): Promise<{ success: boolean }> {
    return this.request(`/upload/chips/${encodeURIComponent(objectName)}`, {
      method: "DELETE",
    });
  }
}

export const api = new ApiService();
export default api;
