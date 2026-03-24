#!/usr/bin/env python3
"""
Build embedding index for satellite imagery.

Usage:
    python build_index.py --metadata-file ./data/metadata/xview_metadata.json --output-dir ./data

This script:
    1. Loads chip metadata
    2. Generates embeddings using CLIP
    3. Stores in ChromaDB
    4. Saves index statistics
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Optional
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import DEVICE, CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME
from app.services.chroma_service import ChromaService
from app.services.dataset_loader import DatasetLoader, IndexBuilder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def build_index(
    metadata_file: str,
    image_dir: Optional[str] = None,
    output_dir: str = "./data",
    batch_size: int = 32,
    device: str = "cpu"
) -> None:
    """Build embedding index.
    
    Args:
        metadata_file: Path to metadata JSON file
        image_dir: Directory containing chip images
        output_dir: Output directory for index
        batch_size: Batch size for embedding generation
        device: Device to use (cuda or cpu)
    """
    logger.info("=" * 80)
    logger.info("Building Satellite Image Index")
    logger.info("=" * 80)
    
    try:
        # Load metadata
        logger.info(f"Loading metadata from {metadata_file}")
        with open(metadata_file, 'r') as f:
            metadata_list = json.load(f)
        logger.info(f"Loaded {len(metadata_list)} chip metadata")
        
        # Initialize ChromaDB
        logger.info("Initializing ChromaDB...")
        chroma_service = ChromaService(
            persist_dir=CHROMA_PERSIST_DIR,
            collection_name=CHROMA_COLLECTION_NAME,
            device=device,
        )
        chroma_service.get_or_create_collection()
        logger.info(f"✓ ChromaDB initialized ({CHROMA_PERSIST_DIR})")
        
        # Initialize dataset loader and index builder
        dataset_loader = DatasetLoader()
        index_builder = IndexBuilder(chroma_service, dataset_loader)
        
        # Build index
        logger.info(f"Building index with {len(metadata_list)} chips...")
        stats = index_builder.build_index_from_metadata(
            metadata_list,
            image_dir=image_dir,
            batch_size=batch_size
        )
        
        logger.info("=" * 80)
        logger.info("Index Statistics")
        logger.info("=" * 80)
        logger.info(f"Total embeddings: {stats['total_embeddings']}")
        logger.info(f"Collection count: {stats['collection_count']}")
        logger.info(f"Embedding backend: {stats['embedding_backend']}")
        logger.info("=" * 80)
        
        # Save stats
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        stats_file = output_path / "index_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        logger.info(f"Saved statistics to {stats_file}")
    
    except Exception as e:
        logger.error(f"Failed to build index: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build embedding index")
    parser.add_argument(
        "--metadata-file",
        type=str,
        default="./data/metadata/xview_metadata.json",
        help="Path to metadata JSON file"
    )
    parser.add_argument(
        "--image-dir",
        type=str,
        default=None,
        help="Directory containing chip images (optional)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data",
        help="Output directory for index"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for embedding generation"
    )
    parser.add_argument(
        "--device",
        type=str,
        default=DEVICE,
        choices=["cuda", "cpu"],
        help="Device to use (cuda or cpu)"
    )
    
    args = parser.parse_args()
    
    build_index(
        metadata_file=args.metadata_file,
        image_dir=args.image_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        device=args.device
    )
