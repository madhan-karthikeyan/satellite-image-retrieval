"""Extract sample images from fMoW dataset for demonstration."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
from PIL import Image


def extract_samples(num_samples: int = 10, split: str = "train"):
    """Extract sample images from fMoW dataset.

    Args:
        num_samples: Number of images to extract
        split: Dataset split to use ('train', 'val', or 'test')
    """
    output_dir = Path(__file__).parent.parent / "sample_images"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading fMoW dataset (split: {split})...")
    dataset = load_dataset(
        "danielz01/fMoW",
        split=split,
        cache_dir="./data/fmow"
    )

    print(f"Dataset loaded: {len(dataset)} samples")
    print(f"Extracting {num_samples} sample images...")

    indices = list(range(0, len(dataset), max(1, len(dataset) // num_samples)))[:num_samples]

    for i, idx in enumerate(indices):
        example = dataset[idx]
        image = example["image"]
        lat = example["lat"]
        lon = example["lon"]
        category = example.get("category", example.get("label", "unknown"))

        filename = f"{split}_{i:03d}_{category.replace(' ', '_')}.jpg"
        filepath = output_dir / filename

        img_rgb = image.convert("RGB")
        img_rgb.save(filepath, quality=85)

        metadata_file = output_dir / f"{split}_{i:03d}_metadata.txt"
        with open(metadata_file, "w") as f:
            f.write(f"Index: {idx}\n")
            f.write(f"Latitude: {lat}\n")
            f.write(f"Longitude: {lon}\n")
            f.write(f"Category: {category}\n")

        print(f"  [{i+1}/{len(indices)}] Saved: {filename} ({lat:.4f}, {lon:.4f}) - {category}")

    print(f"\nExtracted {len(indices)} images to: {output_dir}")
    print("You can use these images to test the inference API:")
    print(f"  curl -X POST http://localhost:8000/infer -F 'image=@{output_dir}/sample_000_airport.jpg'")


def main():
    parser = argparse.ArgumentParser(description="Extract sample images from fMoW dataset")
    parser.add_argument(
        "-n", "--num-samples",
        type=int,
        default=10,
        help="Number of images to extract (default: 10)"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="train",
        choices=["train", "val", "test"],
        help="Dataset split to use"
    )

    args = parser.parse_args()
    extract_samples(num_samples=args.num_samples, split=args.split)


if __name__ == "__main__":
    main()
