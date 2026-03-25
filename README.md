# Satellite Image Retrieval & Analysis Platform

<p align="center">
  <img src="https://img.shields.io/badge/AI-RemoteCLIP-9f7aea?style=for-the-badge" alt="RemoteCLIP">
  <img src="https://img.shields.io/badge/DB-ChromaDB-6366f1?style=for-the-badge" alt="ChromaDB">
  <img src="https://img.shields.io/badge/Frontend-React-61dafb?style=for-the-badge" alt="React">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge" alt="FastAPI">
</p>

> **AI-powered satellite image geolocation system** that extracts precise GPS coordinates from satellite imagery using advanced vision-language models and vector similarity search.

## 🌟 Features

- **Precision Geolocation** - Extract accurate geographic coordinates from satellite images
- **Real-time Processing** - Fast inference with optimized ML pipeline
- **Scene Analysis** - Identify terrain types and land cover classifications
- **Confidence Scoring** - Calibrated confidence metrics for prediction reliability
- **Interactive Globe** - Visualize results on Cesium 3D globe
- **Test-Time Augmentation** - Robust embeddings via multi-view inference
- **Ensemble Retrieval** - Combines multiple search strategies for accuracy
- **Responsive Design** - Mobile-friendly interface for hackathon demos

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌─────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │   Hero  │  │  ImageUpload │  │  CoordinateDisplay     │   │
│  └─────────┘  └──────────────┘  └────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Cesium 3D Globe Visualization               │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬──────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼──────────────────────────────────┐
│                      Backend (FastAPI)                         │
│  ┌─────────────┐  ┌─────────────────┐  ┌──────────────────┐   │
│  │  /infer     │  │  /index/stats   │  │  /infer/batch   │   │
│  └─────────────┘  └─────────────────┘  └──────────────────┘   │
└────────────────────────────┬──────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│                      ML Service (SatGeoInfer)                  │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────────┐   │
│  │   Embedder   │  │  Retriever │  │    Clustering      │   │
│  │  RemoteCLIP  │  │  ChromaDB   │  │    DBSCAN+TTA     │   │
│  └──────────────┘  └─────────────┘  └────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
satellite-image-retrieval/
├── frontend/                     # React + TypeScript frontend
│   ├── src/
│   │   ├── components/          # UI components
│   │   │   ├── Hero.tsx         # Landing section
│   │   │   ├── Globe.tsx        # Cesium 3D globe
│   │   │   ├── ImageUpload.tsx  # Drag-drop upload
│   │   │   ├── CoordinateDisplay.tsx  # Results display
│   │   │   ├── FeatureCards.tsx # Feature showcase
│   │   │   ├── StatsSection.tsx # Statistics display
│   │   │   └── HowItWorks.tsx   # Process explanation
│   │   ├── pages/
│   │   │   └── GlobePage.tsx    # Full globe view
│   │   ├── services/
│   │   │   └── api.ts          # API client
│   │   └── types/
│   │       └── index.ts        # TypeScript interfaces
│   ├── tailwind.config.js       # Tailwind CSS config
│   └── package.json
├── ml-service/                   # Python FastAPI backend
│   ├── app/
│   │   ├── main.py             # API routes
│   │   └── routes/
│   │       └── infer.py        # Inference endpoints
│   ├── satgeoinfer/             # Core ML library
│   │   ├── embedder.py         # RemoteCLIP embedding
│   │   ├── retriever.py         # ChromaDB retrieval
│   │   ├── pipeline.py          # Inference pipeline
│   │   ├── clustering.py        # Geographic clustering
│   │   ├── confidence.py        # Confidence estimation
│   │   └── utils.py             # Utilities
│   ├── scripts/
│   │   ├── build_index.py       # Index building
│   │   └── evaluate.py          # Evaluation script
│   └── requirements.txt
├── docker-compose.yml            # Docker orchestration
├── Dockerfile                    # Container config
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- NVIDIA GPU (optional, for faster inference)
- Cesium Ion token (free at https://cesium.com/ion/)

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/satellite-image-retrieval.git
cd satellite-image-retrieval
```

### 2. Frontend Setup

```bash
cd frontend
npm install

# Create environment file
cp .env.example .env

# Edit .env and add your Cesium token
# VITE_CESIUM_TOKEN=your-token-here

npm run dev
```

### 3. Backend Setup

```bash
cd ml-service
pip install -r requirements.txt

# Build the index (requires ~20GB free space)
python scripts/build_index.py --split train --batch-size 16

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### 4. Docker Setup (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run individually
docker build -t satintel-backend ./ml-service
docker run -p 8000:8000 satintel-backend
```

## 🔧 Configuration

### Environment Variables

**Frontend (`.env`):**
```bash
VITE_API_URL=http://localhost:8000
VITE_CESIUM_TOKEN=your-cesium-ion-token
```

**Backend (`.env`):**
```bash
ADMIN_API_KEY=your-secure-admin-key
CHROMA_PERSIST_DIR=./chroma_index
OPENROUTER_KEY=sk-... # Optional, for AI explanations
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /infer` | POST | Single image geolocation inference |
| `POST /infer/batch` | POST | Batch inference (max 20 images) |
| `GET /infer/stats` | GET | Inference statistics |
| `GET /infer/health` | GET | Service health check |
| `GET /index/stats` | GET | ChromaDB index statistics |
| `POST /index/build` | POST | Trigger index building (admin) |

### API Response Example

```json
{
  "status": "success",
  "centroid_lat": 40.7128,
  "centroid_lon": -74.0060,
  "confidence_radius_km": 150.5,
  "confidence_level": "high",
  "confidence_score": 0.85,
  "cluster_size": 15,
  "total_candidates": 100,
  "scene_distribution": {
    "urban": 8,
    "residential": 5,
    "commercial": 2
  },
  "secondary_clusters": [
    {"centroid_lat": 41.2, "centroid_lon": -73.8, "size": 3}
  ],
  "similarity_stats": {
    "mean": 0.75,
    "min": 0.62,
    "max": 0.89,
    "std": 0.08,
    "q25": 0.68,
    "q75": 0.82
  }
}
```

## 🤖 ML Pipeline

### Embedding Model

- **Model**: RemoteCLIP-ViT-L-14
- **Dimensions**: 768
- **Normalization**: L2-normalized
- **Augmentation**: 8x Test-Time Augmentation (TTA)

### Retrieval System

- **Vector DB**: ChromaDB (persistent)
- **Index Size**: ~20,000 fMoW images
- **Fusion**: Reciprocal Rank Fusion (RRF)
- **Fallback**: Adaptive threshold relaxation

### Clustering

- **Algorithm**: DBSCAN with Haversine metric
- **Epsilon**: Adaptive (95th percentile k-NN distance)
- **Outlier Removal**: Iterative distance-based filtering
- **Centroid**: Weighted 3D Cartesian (antimeridian-safe)

## 📊 Evaluation

Run evaluation script to measure accuracy:

```bash
cd ml-service
python scripts/evaluate.py --split test --sample-size 500 --compare
```

**Metrics Tracked:**
- Mean/Median/P75/P90/P95 geolocation error (km)
- Accuracy@25km, @50km, @100km, @200km, @500km
- Confidence calibration
- Per-scene performance

## 🎨 UI Features

### Home Page
- Animated hero section with gradient text
- Statistics display with animated counters
- Feature cards with hover effects
- Step-by-step process explanation

### Upload Section
- Drag-and-drop with visual feedback
- File validation (type, size)
- Image preview with loading states
- Error handling with retry option

### Results Display
- Latitude/Longitude with high precision
- Confidence score with visual progress bar
- Scene distribution breakdown
- Copy-to-clipboard functionality
- Interactive globe visualization

## 🛠️ Development

### Run Tests

```bash
# Frontend
cd frontend && npm test

# Backend
cd ml-service && pytest
```

### Build for Production

```bash
# Frontend
cd frontend && npm run build

# Backend
cd ml-service && uvicorn app.main:app --prod
```

## 📝 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- [RemoteCLIP](https://github.com/chendelong/RemoteCLIP) - Remote sensing vision-language model
- [fMoW Dataset](https://github.com/fMoW/dataset) - Functional Map of the World dataset
- [ChromaDB](https://www.trychroma.com/) - Vector database for embeddings
- [Cesium](https://cesium.com/) - 3D geospatial visualization

## 📮 Contact

For questions or collaboration:
- GitHub Issues: [Open an issue](https://github.com/yourusername/satellite-image-retrieval/issues)
- Email: your.email@example.com
