# Satellite Image Visual Search Backend

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/upload/chip` - Upload image chip
- `POST /api/upload/chip-from-box` - Upload chip from drawn box
- `GET /api/imagery/list?directory=/path/to/images` - List satellite imagery
- `POST /api/search/execute` - Execute visual search
- `POST /api/search/batch` - Batch search
