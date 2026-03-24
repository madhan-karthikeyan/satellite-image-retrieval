# Satellite Visual Search

PS-03: Visual Search, Retrieval & Detection in Satellite Imageries

## Quick Start

### Frontend (Vite + React)
```bash
cd apps
pnpm install
pnpm dev:web
# Runs at http://localhost:3001
```

### Backend (FastAPI + ChromaDB)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Runs at http://localhost:8000
```

## Features
- Upload image chips or draw boxes on satellite imagery
- Visual search with similarity matching
- ChromaDB vector storage for embeddings
- Dark themed UI with Space Grotesk font

## Tech Stack
- Frontend: React, Vite, TanStack Router, TailwindCSS
- Backend: FastAPI, ChromaDB, PyTorch, rasterio
