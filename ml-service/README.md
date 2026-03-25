# SatGeoInfer

Retrieval-based satellite image geolocation system using RemoteCLIP and ChromaDB.

## Overview

SatGeoInfer is a production-ready system for inferring geographic location from satellite imagery. It uses:

- **RemoteCLIP** (`chendelong/RemoteCLIP-ViT-L-14`) for image embeddings
- **ChromaDB** for vector similarity search
- **DBSCAN** with Haversine metric for geographic clustering
- **FastAPI** for REST API inference

## Project Structure

```
satgeoinfer/
├── app/                    # FastAPI application
│   ├── main.py            # API entry point
│   ├── routes/            # API routes
│   │   └── infer.py       # Inference endpoint
│   └── models/            # Pydantic response models
├── satgeoinfer/           # Core library
│   ├── pipeline.py        # Main inference pipeline
│   ├── embedder.py        # RemoteCLIP embedder
│   ├── retriever.py       # ChromaDB retriever
│   ├── clustering.py      # DBSCAN clustering
│   ├── confidence.py      # Confidence estimation
│   └── utils.py           # Utility functions
├── scripts/
│   ├── download_dataset.py   # Download fMoW dataset
│   └── build_index.py        # Build ChromaDB index
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### 1. Download Dataset

```bash
python scripts/download_dataset.py
```

### 2. Build Index

```bash
python scripts/build_index.py --split train
```

### 3. Run API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Query Inference

```bash
curl -X POST "http://localhost:8000/infer" \
  -F "image=@path/to/satellite_image.jpg" \
  -F "explain=true"
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/infer` | POST | Perform geolocation inference |
| `/infer/batch` | POST | Batch inference (multiple images) |
| `/index/stats` | GET | Get index statistics |
| `/index/build` | POST | Trigger index building (admin only) |
| `/health` | GET | Health check |

## Configuration

Environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | No | - | API key for explanations |
| `OPENAI_BASE_URL` | No | OpenAI | Custom API endpoint |
| `CHROMA_PERSIST_DIR` | No | `./chroma_index` | ChromaDB storage path |
| `ADMIN_API_KEY` | For `/index/build` | - | Admin key for protected endpoints |

### Admin Endpoint Usage

```bash
# Build index with admin key
curl -X POST "http://localhost:8000/index/build?split=train" \
  -H "X-Admin-Key: your-admin-api-key"
```

## Response Format

```json
{
  "status": "success",
  "centroid_lat": 40.7128,
  "centroid_lon": -74.0060,
  "confidence_radius_km": 250.5,
  "confidence_level": "high",
  "cluster_size": 15,
  "total_candidates": 100,
  "scene_distribution": {
    "urban": 8,
    "residential": 5,
    "commercial": 2
  },
  "secondary_clusters": [
    {
      "centroid_lat": 40.7589,
      "centroid_lon": -73.9851,
      "size": 3
    }
  ],
  "explanation": "The image shows urban features..."
}
```

## Confidence Levels

| Level | Radius | Size | Mean Similarity | Min Similarity |
|-------|--------|------|-----------------|----------------|
| **high** | ≤300km | ≥5 | ≥0.75 | ≥0.60 |
| **medium** | ≤800km | ≥3 | ≥0.65 or Q25≥0.55 |
| **low** | else | - | - | - |

## Architecture Highlights

### ChromaDB Distance Conversion
Correctly converts squared L2 distance to cosine similarity:
```
cosine_sim = 1 - (distance / 2)
```

### Antimeridian-Safe Centroid
Uses 3D Cartesian averaging to handle longitude wrap-around at ±180°.

### Dominant Cluster Selection
Selected by total similarity weight, not raw count.

### Adaptive Retrieval
Configurable retry schedule expands search if initial results are sparse.

## Roadmap

### 🔴 Critical Priority

1. **SatCLIP Integration** (HIGHEST LEVERAGE)
   - RemoteCLIP is trained for scene understanding, not geographic localization
   - SatCLIP embeddings encode geographic location as a primary signal
   - Would directly improve retrieval precision
   - Reference: [SatCLIP](https://github.com/microsoft/GeospatialCLIP)

### 🟠 High Priority

2. **FAISS Backend Option**
   - Sub-millisecond queries at scale
   - Lower memory footprint for millions of vectors
   - Optional: keep ChromaDB for metadata filtering

3. **Geographic Pre-filtering**
   - Add bounding box filter to retrieval
   - Enable region-specific queries

### 🟡 Medium Priority

4. **Batch Processing Pipeline**
   - GPU-accelerated batch embedding
   - Parallel ChromaDB writes

5. **Caching Layer**
   - Cache frequent query embeddings
   - LRU cache for retrieval results

6. **Metrics & Observability**
   - Query latency tracking
   - Retrieval quality metrics
   - Confidence calibration curves

### 🟢 Nice to Have

7. **Multi-modal Queries**
   - Text + image search
   - Satellite metadata filtering

8. **Incremental Index Updates**
   - Stream new images to index
   - Update existing embeddings

## License

MIT
