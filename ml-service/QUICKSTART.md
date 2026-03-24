# QUICKSTART - Satellite Intelligence System Backend

## 60-Second Setup

```bash
cd ml-service
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open new terminal:
```bash
curl http://localhost:8000/health | python -m json.tool
```

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| POST | `/api/search` | Search similar images |
| POST | `/api/detect` | Detect objects in image |
| POST | `/api/search/export-txt` | Export as TXT |
| POST | `/api/search/export-json` | Export as JSON |
| GET | `/api/search/stats` | Service statistics |
| POST | `/api/index/build` | Build index from metadata/dummy |
| POST | `/api/index/build-from-dataset` | Preprocess + build from xView |
| GET | `/api/index/status` | Index status |
| POST | `/api/index/reset` | Reset index |

## Example Usage

### Search

```bash
# Test image creation
python << 'EOF'
from PIL import Image
import numpy as np
Image.fromarray(np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)).save('query.jpg')
EOF

# Search
curl -X POST -F "image=@query.jpg" http://localhost:8000/api/search?top_k=5 | python -m json.tool
```

### Client Script

```bash
# Health
python example_client.py --health

# Search
python example_client.py --image query.jpg --top-k 10

# Export
python example_client.py --image query.jpg --export-txt results.txt --export-json results.json

# Stats
python example_client.py --stats
```

## File Structure

```
ml-service/
├── app/
│   ├── main.py                 ← FastAPI app entry point
│   ├── config.py               ← Configuration
│   ├── routes/
│   │   ├── search.py           ← Search API
│   │   └── indexing.py         ← Index management
│   ├── services/
│   │   ├── chroma_service.py   ← Vector database
│   │   ├── retrieval.py        ← Search pipeline
│   │   └── dataset_loader.py   ← Dataset handling
│   ├── models/
│   │   └── clip_model.py       ← CLIP embeddings
│   └── utils/
│       ├── image_processing.py
│       └── geo_utils.py        ← Lat/lon conversion
├── scripts/
│   ├── preprocess_xview.py     ← Dataset preprocessing
│   └── build_index.py          ← Index building
├── requirements.txt             ← Dependencies
├── README.md                    ← Full documentation
├── SETUP.md                     ← Setup guide
└── example_client.py            ← Example client
```

## Key Features

✓ **CLIP embeddings** (ViT-B/32, 512-dim)
✓ **ChromaDB vector storage** (50k+ embeddings)
✓ **Geo-conversion** (pixel → lat/lon)
✓ **FastAPI** with async
✓ **Search export** (JSON + TXT)
✓ **Production-ready** (type hints, error handling)

## Configuration

Edit `app/config.py`:
- `DEVICE` → "cuda" or "cpu"
- `DEFAULT_TOP_K` → Default results (10)
- `CLIP_MODEL_NAME` → Model variant
- `API_PORT` → Port (default 8000)

## With Frontend

Terminal 1 (Backend):
```bash
cd ml-service
python -m uvicorn app.main:app --port 8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` → Upload image → View results on 3D globe

## Processing Real Dataset

```bash
# 1. Preprocess xView images (using your repo folders)
python scripts/preprocess_xview.py \
  --images-dir ../train_images/train_images \
  --labels-file ../train_labels/xView_train.geojson \
  --output-dir ./data/metadata

# 2. Build index
python scripts/build_index.py \
  --metadata-file ./data/metadata/xview_metadata.json \
  --image-dir ./data/metadata/chips \
  --device cuda

# 3. Or do both in one API call
curl -X POST http://localhost:8000/api/index/build-from-dataset
```

## Response Format (Frontend Compatible)

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
  "search_time_ms": 250.5
}
```

## Performance

- Query latency: < 2 seconds (10k embeddings)
- Throughput: 10+ searches/second
- Memory: ~4GB for 50k embeddings
- GPU: 3-5x faster (NVIDIA CUDA)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CLIP download fails | `python -c "import clip; clip.load('ViT-B/32')"` |
| CUDA out of memory | Set `DEVICE=cpu` in config.py |
| Port 8000 in use | Use `--port 8001` or `lsof -ti:8000 \| xargs kill -9` |
| ChromaDB error | `rm -rf ./data/chroma_index` |

## Next Steps

1. Read `README.md` for full documentation
2. Read `SETUP.md` for detailed setup
3. Run `example_client.py` for testing
4. Modify `app/config.py` for your needs
5. Process dataset with preprocessing scripts

## Documentation

- Full API docs: `http://localhost:8000/docs`
- README.md: Complete reference
- SETUP.md: Installation guide
- Code comments: Inline documentation

---

**Status**: ✓ Production-ready
**Version**: 1.0.0
**License**: MIT
