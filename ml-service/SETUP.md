# Setup Instructions - Satellite Intelligence System

## Complete Setup Guide

### Prerequisites

- Python 3.9+
- pip or conda
- 8GB+ RAM (16GB+ recommended)
- NVIDIA GPU with CUDA support (optional, recommended for speed)

### Step 1: Clone/Navigate to Project

```bash
cd ml-service
```

### Step 2: Create Virtual Environment (Optional but Recommended)

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n sat-backend python=3.10
conda activate sat-backend
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**If CLIP fails to install:**
```bash
pip install torch torchvision
pip install git+https://github.com/openai/CLIP.git
pip install chromadb numpy opencv-python pillow fastapi uvicorn pydantic python-multipart
```

### Step 4: Verify Installation

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}')"
python -c "import clip; model, preprocess = clip.load('ViT-B/32', device='cpu'); print('CLIP loaded successfully')"
python -c "import chromadb; print('ChromaDB loaded successfully')"
```

### Step 5: Run Backend

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
================================================================================
Satellite Intelligence System - Backend Starting
================================================================================
...
✓ CLIP model loaded
✓ ChromaDB initialized
✓ Retrieval service initialized
✓ Index builder initialized
✓ Detection service initialized
✓ Real index built ... OR Dummy index built ...
================================================================================
Backend Ready!
================================================================================
```

### Step 6: Test API (New Terminal)

```bash
# Health check
curl http://localhost:8000/health

# You should get:
# {
#   "status": "healthy",
#   "service": "Satellite Intelligence System",
#   "components": {...},
#   "index_status": {"total_embeddings": 50}
# }
```

### Step 7: Run Example Client

```bash
# Show help
python example_client.py --help

# Health check
python example_client.py --health

# Show statistics
python example_client.py --stats

# Show index status
python example_client.py --status
```

## Full Setup with Real Data

### 1. Prepare Dataset

```bash
# Create demo image
python << 'EOF'
from PIL import Image
import numpy as np

# Create random satellite-like image
img_array = np.random.randint(50, 200, (512, 512, 3), dtype=np.uint8)
img_array[100:200, 100:200] = np.random.randint(100, 255, (100, 100, 3), dtype=np.uint8)

Image.fromarray(img_array).save('test_image.jpg')
print("Created test_image.jpg")
EOF
```

### 2. Test Search

```bash
# Basic search
python example_client.py --image test_image.jpg

# Search with more results
python example_client.py --image test_image.jpg --top-k 20

# Export results
python example_client.py --image test_image.jpg --export-txt results.txt --export-json results.json
```

### 3. Using with Frontend

The frontend is already configured to connect to the backend. Start both:

**Terminal 1 - Backend:**
```bash
cd ml-service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` and upload an image. Results will display on the 3D globe.

## Dataset Processing (Advanced)

### Process xView Dataset

If you have the xView dataset:

```bash
# 1. Preprocess images into chips (repo paths)
python scripts/preprocess_xview.py \
  --images-dir ../train_images/train_images \
  --labels-file ../train_labels/xView_train.geojson \
  --output-dir ./data/metadata \
  --chip-size 512 \
  --max-images 1000

# 2. Build embeddings index
python scripts/build_index.py \
  --metadata-file ./data/metadata/xview_metadata.json \
  --image-dir ./data/metadata/chips \
  --batch-size 32 \
  --device cuda

# 3. Or run preprocessing + indexing from API
curl -X POST http://localhost:8000/api/index/build-from-dataset
```

## Configuration

Edit `app/config.py` to customize:

```python
# Model selection
CLIP_MODEL_NAME = "ViT-B/32"  # Options: ViT-B/32, ViT-L/14, ViT-L/14@336px

# Hardware
DEVICE = "cuda"  # or "cpu"

# Search parameters
DEFAULT_TOP_K = 10
MIN_SIMILARITY_THRESHOLD = 0.3

# API
API_PORT = 8000
API_HOST = "0.0.0.0"
```

## Environment Variables

```bash
export API_PORT=8000
export DEVICE=cuda  # or cpu
export DEBUG=False
export LOG_LEVEL=INFO
```

## Troubleshooting

### Issue: CLIP download fails
**Solution:**
```bash
# Pre-download model
python -c "import clip; clip.load('ViT-B/32')"

# Or force CPU mode
export DEVICE=cpu
```

### Issue: CUDA out of memory
**Solution:**
```python
# In app/config.py
DEVICE = "cpu"  # Use CPU instead
MAX_BATCH_SIZE = 8  # Reduce batch size
```

### Issue: Port 8000 already in use
**Solution:**
```bash
# Use different port
python -m uvicorn app.main:app --port 8001

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

### Issue: ChromaDB persistence error
**Solution:**
```bash
# Reset ChromaDB
rm -rf ./data/chroma_index
python -m uvicorn app.main:app --port 8000
```

### Issue: Slow inference
**Optimization:**
- Enable CUDA: `DEVICE=cuda`
- Increase batch size: `MAX_BATCH_SIZE=64`
- Use lighter model: `CLIP_MODEL_NAME=ViT-B/32` (default, fastest)

## API Testing

### Using cURL

```bash
# 1. Health check
curl http://localhost:8000/health | jq

# 2. Create test image
python << 'EOF'
from PIL import Image
import numpy as np
Image.fromarray(np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)).save('query.jpg')
EOF

# 3. Search
curl -X POST -F "image=@query.jpg" http://localhost:8000/api/search | jq

# 4. Export results
curl -X POST -F "image=@query.jpg" http://localhost:8000/api/search/export-txt > results.txt

# 5. Get stats
curl http://localhost:8000/api/search/stats | jq
```

### Using Python requests

```python
import requests
from pathlib import Path

# Create test image
from PIL import Image
import numpy as np
Image.fromarray(np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)).save('query.jpg')

# Search
with open('query.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/search',
        files={'image': f},
        params={'top_k': 10, 'threshold': 0.3}
    )

results = response.json()
print(f"Found {results['count']} results")
for r in results['results'][:3]:
    print(f"  {r['chip_id']}: {r['lat']:.4f}, {r['lon']:.4f} (score: {r['score']:.3f})")
```

## Production Deployment

### Docker Deployment

```dockerfile
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3.10 python3-pip

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ app/
COPY scripts/ scripts/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t sat-backend:latest .
docker run -d -p 8000:8000 --gpus all --name sat-backend sat-backend:latest
```

### Monitor Logs

```bash
# Docker
docker logs -f sat-backend

# Local
tail -f logs/backend.log
```

## Next Steps

1. **Prepare data**: Use `preprocess_xview.py` to process your dataset
2. **Build index**: Use `build_index.py` to create embeddings
3. **Deploy**: Use Docker or cloud deployment
4. **Monitor**: Check logs and API stats regularly

## Support

For issues, check:
- `app/config.py` for configuration
- `logs/backend.log` for error details
- API documentation at `http://localhost:8000/docs`
