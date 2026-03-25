"""Build ChromaDB index from fMoW dataset."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
from tqdm import tqdm

from satgeoinfer.embedder import Embedder
from satgeoinfer.retriever import Retriever


def build_index(split: str = "train", batch_size: int = 64):
    """Build ChromaDB index from fMoW dataset.

    Args:
        split: Dataset split to index ('train', 'val', or 'test')
        batch_size: Batch size for embedding generation
    """
    print(f"Loading fMoW dataset (split: {split})...")
    dataset = load_dataset(
        "danielz01/fMoW",
        split=split,
        cache_dir="./data/fmow"
    )

    print(f"Dataset loaded: {len(dataset)} samples")

    print("Initializing embedder...")
    embedder = Embedder()

    print("Initializing retriever...")
    retriever = Retriever()

    indexed_ids = retriever.get_all_ids()
    print(f"Already indexed: {len(indexed_ids)} samples")

    total = len(dataset)
    processed = 0
    skipped = 0

    print(f"Processing {total} images in batches of {batch_size}...")

    for i in tqdm(range(0, total, batch_size), desc="Building index"):
        batch_end = min(i + batch_size, total)
        batch = dataset.select(range(i, batch_end))

        for idx, example in enumerate(batch):
            global_idx = i + idx
            image_id = f"{split}_{global_idx}"

            if image_id in indexed_ids:
                skipped += 1
                continue

            image = example["image"]
            lat = example["lat"]
            lon = example["lon"]
            category = example.get("category", example.get("label", "unknown"))

            try:
                pixel_values = embedder.preprocess(image)
                embedding = embedder.embed(pixel_values)

                retriever.store(
                    image_id=image_id,
                    embedding=embedding,
                    lat=lat,
                    lon=lon,
                    scene_label=category
                )

                processed += 1

            except Exception as e:
                print(f"Error processing {image_id}: {e}")
                continue

    print(f"\nIndexing complete!")
    print(f"  Processed: {processed}")
    print(f"  Skipped: {skipped}")
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
        default=64,
        help="Batch size for embedding generation"
    )

    args = parser.parse_args()

    build_index(split=args.split, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
