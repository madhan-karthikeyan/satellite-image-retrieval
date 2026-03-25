"""Build ChromaDB index from fMoW dataset with optimized batch processing."""

import os
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')

import argparse
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from functools import partial

sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
from tqdm import tqdm
import torch

from satgeoinfer.embedder import Embedder
from satgeoinfer.retriever import Retriever


def _preprocess_item(preprocess_fn, item):
    """Preprocess a single item."""
    return preprocess_fn(item['image'])


def build_index(
    split: str = "train",
    batch_size: int = 32,
    num_workers: int = 4,
    prefetch_factor: int = 2
):
    """Build ChromaDB index from fMoW dataset with optimized batch processing.
    
    Args:
        split: Dataset split to index ('train', 'val', or 'test')
        batch_size: Batch size for embedding generation
        num_workers: Number of preprocessing workers
        prefetch_factor: Number of batches to prefetch
    """
    print(f"Loading fMoW dataset (split: {split})...")
    dataset = load_dataset(
        "danielz01/fMoW",
        split=split,
        cache_dir="./data/fmow"
    )

    print(f"Dataset loaded: {len(dataset)} samples")

    print("Initializing embedder (GPU)...")
    embedder = Embedder(use_tta=False)
    print(f"Using device: {embedder.device}")

    print("Initializing retriever...")
    retriever = Retriever()

    indexed_ids = retriever.get_all_ids()
    print(f"Already indexed: {len(indexed_ids)} samples")

    total = len(dataset)
    processed = 0
    skipped = 0
    errors = 0
    start_time = time.time()
    preprocess_fn = embedder._preprocess_fn

    print(f"Processing {total} images in batches of {batch_size}...")
    print("=" * 60)

    with torch.no_grad():
        for i in tqdm(range(0, total, batch_size), desc="Building index"):
            batch_end = min(i + batch_size, total)
            batch = dataset.select(range(i, batch_end))

            batch_data = []
            
            for idx, example in enumerate(batch):
                global_idx = i + idx
                image_id = f"{split}_{global_idx}"

                if image_id in indexed_ids:
                    skipped += 1
                    continue

                try:
                    batch_data.append({
                        'id': image_id,
                        'image': example['image'],
                        'lat': example['lat'],
                        'lon': example['lon'],
                        'category': example.get('category', example.get('label', 'unknown'))
                    })
                except Exception as e:
                    errors += 1
                    continue

            if not batch_data:
                continue

            try:
                preprocessed = []
                for item in batch_data:
                    try:
                        processed_tensor = preprocess_fn(item['image'])
                        preprocessed.append(processed_tensor)
                    except Exception:
                        continue
                
                if not preprocessed:
                    errors += len(batch_data)
                    continue
                
                batch_tensor = torch.cat(preprocessed, dim=0).to(embedder.device)
                
                with torch.cuda.amp.autocast(enabled=embedder.device == 'cuda'):
                    image_features = embedder.model.encode_image(batch_tensor)
                    image_features = torch.nn.functional.normalize(image_features, dim=-1)
                    embeddings = image_features.cpu().tolist()
                
                batch_tensor = batch_tensor.to('cpu')
                del batch_tensor
                
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                for j, item in enumerate(batch_data[:len(embeddings)]):
                    retriever.store(
                        image_id=item['id'],
                        embedding=embeddings[j],
                        lat=item['lat'],
                        lon=item['lon'],
                        scene_label=item['category']
                    )
                    processed += 1

                if processed % 500 == 0 and processed > 0:
                    elapsed = time.time() - start_time
                    rate = processed / elapsed
                    remaining = total - processed - skipped - errors
                    eta = remaining / rate if rate > 0 else 0
                    print(f"\n  Progress: {processed} processed | {rate:.1f} img/s | ETA: {eta/60:.1f} min")

            except Exception as e:
                errors += len(batch_data)
                print(f"\nError in batch {i}: {e}")
                continue

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"Indexing complete!")
    print(f"  Processed: {processed}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print(f"  Average speed: {processed/elapsed:.1f} images/second")
    print(f"  Total in collection: {retriever.get_collection_size()}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build ChromaDB index from fMoW dataset")
    parser.add_argument(
        "--split",
        type=str,
        default="train",
        choices=["train", "val", "test"],
        help="Dataset split to index"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for GPU (16-32 recommended for 4GB VRAM)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of preprocessing workers"
    )

    args = parser.parse_args()
    build_index(
        split=args.split,
        batch_size=args.batch_size,
        num_workers=args.workers
    )


if __name__ == "__main__":
    main()
