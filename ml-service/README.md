# Satellite Intelligence System - Backend

Production-grade FastAPI backend for satellite image visual search with CLIP embeddings and ChromaDB vector database.

## Features

- **OpenCLIP Embeddings via Chroma**: ViT-B-32 + `laion2b_s34b_b79k`
- **Vector Database**: ChromaDB for efficient similarity search (50k+ embeddings)
- **Geo-conversion**: Pixel coordinates to lat/lon conversion with metadata
- **RESTful API**: FastAPI with async processing
- **Search Results Export**: JSON and evaluation TXT formats
- **Index Management**: Build, query, and reset endpoints
- **Production-Ready**: Type hints, error handling, logging

## Quick Start

### 1. Install Dependencies

```bash
cd ml-service
pip install -r requirements.txt
```

OpenCLIP is used through Chroma's `OpenCLIPEmbeddingFunction`; no manual `clip` package wiring is required.

### 2. Run Backend

```bash
cd ml-service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or directly:
```bash
python -c "from app.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"
```

### 3. Test API

```bash
# Health check
curl http://localhost:8000/health

# Search (POST image)
curl -X POST -F "image=@test_image.jpg" http://localhost:8000/api/search

# Index status
curl http://localhost:8000/api/index/status

# Build dummy index
curl -X POST http://localhost:8000/api/index/build

# Build from real xView dataset in this repo
curl -X POST http://localhost:8000/api/index/build-from-dataset

# Get stats
curl http://localhost:8000/api/search/stats
```

## Project Structure

```
ml-service/
├── app/
│   ├── main.py                 # FastAPI app, startup/shutdown
│   ├── config.py               # Configuration
│   ├── routes/
│   │   ├── search.py           # /api/search endpoints
│   │   └── indexing.py         # /api/index endpoints
│   ├── services/
│   │   ├── embedding.py        # CLIP embeddings (optional)
│   │   ├── chroma_service.py   # ChromaDB wrapper
│   │   ├── retrieval.py        # Search pipeline
│   │   └── dataset_loader.py   # Dataset management
│   ├── models/
│   │   └── clip_model.py       # CLIP model wrapper
│   ├── utils/
│   │   ├── image_processing.py # Image loading/validation
│   │   └── geo_utils.py        # Lat/lon conversion
│   └── config.py               # Configuration
├── scripts/
│   ├── preprocess_xview.py     # Dataset preprocessing
│   └── build_index.py          # Index building
├── data/                        # Data directory (auto-created)
│   ├── chroma_index/           # ChromaDB persistence
│   └── metadata/               # Metadata files
└── requirements.txt             # Dependencies
```

## API Endpoints

### Search Endpoints

#### POST /api/search
Search for similar satellite images

**Parameters:**
- `image` (File): Query satellite image
- `top_k` (int, default=10): Number of results
- `threshold` (float, default=0.3): Minimum similarity

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "chip_id": "chip_000001",
      "lat": 37.7749,
      "lon": -122.4194,
      "score": 0.92,
      "image_name": "xview_scene_001.tif",
      "bbox": [100, 200, 300, 400],
      "confidence": 0.92
    }
  ],
  "count": 10,
  "search_time_ms": 245.5
}
```

#### POST /api/detect
Run detection on input image and return candidate boxes/scores

**Response:**
```json
{
  "success": true,
  "count": 3,
  "detections": [
    {
      "bbox": [120, 240, 180, 300],
      "score": 0.78,
      "label": "object",
      "label_id": 0,
      "center": [150.0, 270.0]
    }
  ]
}
```

#### POST /api/search/export-txt
Export results in evaluation format

**Format:**
```
x_min y_min x_max y_max object_name image_name similarity_score
100 200 300 400 chip_001 xview_001.tif 0.920000
```

#### POST /api/search/export-json
Export results as JSON

#### GET /api/search/stats
Get search service statistics

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_embeddings": 50000,
    "cache_size": 245,
    "clip_model_info": {
      "model_name": "ViT-B/32",
      "device": "cuda",
      "embedding_dim": 512,
      "model_parameters": 149000000
    }
  }
}
```

### Index Endpoints

#### POST /api/index/build
Build embedding index from `data/metadata/xview_metadata.json` if present, otherwise fallback to dummy data

#### POST /api/index/build-from-dataset
Preprocess real xView dataset from repo folders (`train_images/train_images` + `train_labels/xView_train.geojson`) and build index

#### GET /api/index/status
Get current index status

**Response:**
```json
{
  "success": true,
  "status": {
    "total_embeddings": 50000,
    "collection_name": "satellite_chips"
  }
}
```

#### POST /api/index/reset
Reset/delete all embeddings

### Health

#### GET /health
Health check

**Response:**
```json
{
  "status": "healthy",
  "service": "Satellite Intelligence System",
  "components": {
    "clip_model": true,
    "chroma_service": true,
    "retrieval_service": true,
    "index_builder": true
  },
  "index_status": {
    "total_embeddings": 50000
  }
}
```

## Data Preprocessing

### 1. Preprocess xView Dataset

```bash
python scripts/preprocess_xview.py \
  --images-dir ../train_images/train_images \
  --labels-file ../train_labels/xView_train.geojson \
  --output-dir ./data/metadata \
  --chip-size 512 \
  --max-images 1000
```

This:
- Splits images into 512x512 chips
- Uses real xView train labels (`bounds_imcoords` + polygon geometry)
- Infers per-image geo extent from labeled objects
- Saves metadata to `data/metadata/xview_metadata.json`
- Saves chip images to `data/metadata/chips/`

Or trigger the full dataset build directly from API:

```bash
curl -X POST http://localhost:8000/api/index/build-from-dataset
```

### 2. Build Index

```bash
python scripts/build_index.py \
  --metadata-file ./data/metadata/xview_metadata.json \
  --image-dir ./data/metadata/chips \
  --batch-size 32 \
  --device cuda
```

This:
- Loads metadata
- Generates CLIP embeddings
- Stores in ChromaDB
- Saves statistics

## Configuration

Edit `app/config.py`:

```python
# Model
CLIP_MODEL_NAME = "ViT-B/32"  # or "ViT-L/14", "ViT-L/14@336px"
EMBEDDING_DIM = 512

# ChromaDB
CHROMA_COLLECTION_NAME = "satellite_chips"
CHROMA_PERSIST_DIR = "./data/chroma_index"

# Search
DEFAULT_TOP_K = 10
MIN_SIMILARITY_THRESHOLD = 0.3
MAX_BATCH_SIZE = 32

# API
API_PORT = 8000
DEVICE = "cuda"  # or "cpu"
```

## Usage Examples

### Python Client

```python
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Search
image_path = "test_image.jpg"
with open(image_path, 'rb') as f:
    files = {'image': f}
    response = requests.post(
        f"{BASE_URL}/api/search?top_k=20&threshold=0.4",
        files=files
    )

results = response.json()
print(f"Found {results['count']} matches")

for result in results['results']:
    print(f"  Chip: {result['chip_id']}")
    print(f"  Location: {result['lat']:.4f}, {result['lon']:.4f}")
    print(f"  Score: {result['score']:.3f}")
```

### JavaScript/Frontend

```javascript
async function searchSatelliteImage(imageFile) {
  const formData = new FormData();
  formData.append('image', imageFile);
  
  const response = await fetch('http://localhost:8000/api/search?top_k=10', {
    method: 'POST',
    body: formData
  });
  
  const results = await response.json();
  return results.results;
}
```

### cURL

```bash
# Upload image and search
curl -X POST \
  -F "image=@query.jpg" \
  -F "top_k=15" \
  "http://localhost:8000/api/search" | jq

# Export results
curl -X POST \
  -F "image=@query.jpg" \
  "http://localhost:8000/api/search/export-txt" > results.txt
```

## Performance

- **Query Latency**: <2 seconds (10k embeddings)
- **Throughput**: 10+ searches/second
- **Memory**: ~4GB for 50k embeddings (CLIP + ChromaDB)
- **GPU**: Optional but recommended (3-5x speedup)

### Optimization Tips

1. **Batch Processing**: Use batch_size=32-64 for index building
2. **GPU Acceleration**: Set DEVICE="cuda" for 3-5x speedup
3. **Embedding Cache**: Automatically caches 500 recent embeddings
4. **Index Partitioning**: Split large datasets across multiple collections

## Geo-Conversion

### Pixel to Lat/Lon

```python
from app.utils.geo_utils import pixel_to_latlon

lat, lon = pixel_to_latlon(
    x=256, y=128,
    width=512, height=512,
    lat_top=85.0, lon_left=-180.0,
    lat_bottom=-85.0, lon_right=180.0
)
```

### Bounding Box to Geo

```python
from app.utils.geo_utils import bbox_to_latlon

bounds = bbox_to_latlon(
    bbox=(100, 200, 300, 400),
    width=512, height=512,
    lat_top=85.0, lon_left=-180.0,
    lat_bottom=-85.0, lon_right=180.0
)
```

## Troubleshooting

### CLIP Model Download Issues

```bash
# Pre-download model
python -c "import clip; clip.load('ViT-B/32')"

# Or download manually
curl -o ViT-B_32.pt https://openaipublic.blob.core.windows.net/clip/models/.../ViT-B_32.pt
```

### CUDA Out of Memory

```python
# Use CPU instead
DEVICE = "cpu"

# Or reduce batch size
MAX_BATCH_SIZE = 8
```

### ChromaDB Persistence

Data is automatically persisted in `./data/chroma_index/`

To reset:
```bash
rm -rf ./data/chroma_index
```

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
black app/ scripts/
isort app/ scripts/
flake8 app/ scripts/
```

### Type Checking

```bash
mypy app/ --strict
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ app/
COPY scripts/ scripts/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t sat-backend .
docker run -p 8000:8000 --gpus all sat-backend
```

### Environment Variables

```bash
export API_PORT=8000
export DEVICE=cuda
export DEBUG=False
export CHROMA_PERSIST_DIR=/data/chroma
```

## Integration with Frontend

Frontend is configured to connect to `http://localhost:8000`:

1. Frontend uploads satellite image
2. Backend returns:
   - `lat/lon` for Cesium visualization
   - `bbox` for debugging
   - `score` for UI display
3. Frontend displays results on 3D globe

## API Response Format for Frontend

```json
{
  "success": true,
  "results": [
    {
      "chip_id": "chip_001",
      "lat": 37.7749,
      "lon": -122.4194,
      "score": 0.92,
      "image_name": "xview_001.tif",
      "bbox": [100, 200, 300, 400],
      "confidence": 0.92
    }
  ],
  "count": 10,
  "search_time_ms": 250
}
```

## License

MIT

## References

- [OpenAI CLIP](https://github.com/openai/CLIP)
- [ChromaDB](https://www.trychroma.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [xView Dataset](https://xviewdataset.org/)
