import os
from pathlib import Path
from typing import Optional

# Base directories
BASE_DIR = Path(__file__).parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
INDEX_DIR = DATA_DIR / "chroma_index"
METADATA_DIR = DATA_DIR / "metadata"
CHIPS_DIR = DATA_DIR / "chips"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)
METADATA_DIR.mkdir(exist_ok=True)
CHIPS_DIR.mkdir(exist_ok=True)

# Model configuration
CLIP_MODEL_NAME = "ViT-B/32"
EMBEDDING_DIM = 512

# ChromaDB configuration
CHROMA_COLLECTION_NAME = "satellite_chips"
CHROMA_PERSIST_DIR = str(INDEX_DIR)

# Image processing
MAX_IMAGE_SIZE = (1024, 1024)
ALLOWED_FORMATS = {"jpg", "jpeg", "png", "tiff", "tif"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# API configuration
API_HOST = "0.0.0.0"
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False") == "True"

# Upload storage
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Search configuration
DEFAULT_TOP_K = 10
MIN_SIMILARITY_THRESHOLD = 0.3
MAX_BATCH_SIZE = 32

# Detection configuration
ENABLE_DETECTION = os.getenv("ENABLE_DETECTION", "True") == "True"
DETECTION_SCORE_THRESHOLD = float(os.getenv("DETECTION_SCORE_THRESHOLD", "0.4"))
DETECTION_MAX_BOXES = int(os.getenv("DETECTION_MAX_BOXES", "20"))

# xView dataset configuration
XVIEW_CHIP_SIZE = 512
XVIEW_CHIP_OVERLAP = 0
XVIEW_METADATA_FILE = METADATA_DIR / "xview_metadata.json"
XVIEW_INDEX_FILE = METADATA_DIR / "xview_index.json"
XVIEW_CHIPS_DIR = CHIPS_DIR

# Default dataset paths (repo-level folders)
XVIEW_TRAIN_IMAGES_DIR = Path(os.getenv("XVIEW_TRAIN_IMAGES_DIR", str(PROJECT_ROOT / "train_images" / "train_images")))
XVIEW_TRAIN_LABELS_FILE = Path(os.getenv("XVIEW_TRAIN_LABELS_FILE", str(PROJECT_ROOT / "train_labels" / "xView_train.geojson")))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "logs" / "backend.log"
LOG_FILE.parent.mkdir(exist_ok=True)

# GPU/CPU configuration
DEVICE = os.getenv("DEVICE", "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu")
