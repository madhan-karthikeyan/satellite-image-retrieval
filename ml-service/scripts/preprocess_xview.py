#!/usr/bin/env python3
"""
Preprocess xView dataset into retrieval chips + metadata.

Inputs:
  - train images directory (e.g. ../train_images/train_images)
  - xView geojson labels (e.g. ../train_labels/xView_train.geojson)

Outputs:
  - chip PNG files
  - metadata JSON for indexing
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
from PIL import Image
from tqdm import tqdm


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_bounds_imcoords(bounds_str: str) -> Optional[Tuple[int, int, int, int]]:
    if not bounds_str or not isinstance(bounds_str, str):
        return None

    if bounds_str.strip().upper() in {"NONE", "NAN", ""}:
        return None

    parts = [p.strip() for p in bounds_str.split(",")]
    if len(parts) != 4:
        return None

    try:
        x_min, y_min, x_max, y_max = [int(float(v)) for v in parts]
    except ValueError:
        return None

    if x_max <= x_min or y_max <= y_min:
        return None
    return x_min, y_min, x_max, y_max


def extract_geo_bounds_from_feature(feature: Dict[str, Any]) -> Optional[Tuple[float, float, float, float]]:
    geometry = feature.get("geometry") or {}
    if geometry.get("type") != "Polygon":
        return None

    coordinates = geometry.get("coordinates")
    if not coordinates or not isinstance(coordinates, list):
        return None

    ring = coordinates[0] if coordinates and isinstance(coordinates[0], list) else []
    if not ring:
        return None

    lons: List[float] = []
    lats: List[float] = []
    for point in ring:
        if not isinstance(point, list) or len(point) < 2:
            continue
        lon = safe_float(point[0], default=np.nan)
        lat = safe_float(point[1], default=np.nan)
        if np.isnan(lon) or np.isnan(lat):
            continue
        lons.append(lon)
        lats.append(lat)

    if not lons or not lats:
        return None

    lat_top = max(lats)
    lat_bottom = min(lats)
    lon_left = min(lons)
    lon_right = max(lons)
    return lat_top, lon_left, lat_bottom, lon_right


def load_xview_label_index(labels_file: Path) -> Dict[str, List[Dict[str, Any]]]:
    with labels_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    by_image: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for feature in tqdm(features, desc="Indexing labels"):
        props = feature.get("properties") or {}
        image_id = props.get("image_id")
        if not image_id:
            continue

        bbox = parse_bounds_imcoords(str(props.get("bounds_imcoords", "")))
        geo_bounds = extract_geo_bounds_from_feature(feature)
        if bbox is None or geo_bounds is None:
            continue

        bbox_tuple: Tuple[int, int, int, int] = bbox
        geo_tuple: Tuple[float, float, float, float] = geo_bounds

        by_image[image_id].append(
            {
                "bbox": bbox_tuple,
                "geo_bounds": geo_tuple,
                "type_id": props.get("type_id"),
                "feature_id": props.get("feature_id"),
            }
        )

    logger.info("Indexed labels for %d images", len(by_image))
    return by_image


def intersects(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1)


def clip_bbox_to_chip(
    obj_bbox: Tuple[int, int, int, int], chip_bbox: Tuple[int, int, int, int]
) -> Optional[Tuple[int, int, int, int]]:
    ox1, oy1, ox2, oy2 = obj_bbox
    cx1, cy1, cx2, cy2 = chip_bbox

    ix1 = max(ox1, cx1)
    iy1 = max(oy1, cy1)
    ix2 = min(ox2, cx2)
    iy2 = min(oy2, cy2)

    if ix2 <= ix1 or iy2 <= iy1:
        return None

    return ix1 - cx1, iy1 - cy1, ix2 - cx1, iy2 - cy1


def pixel_to_geo_from_image_extent(
    x: float,
    y: float,
    image_width: int,
    image_height: int,
    lat_top: float,
    lon_left: float,
    lat_bottom: float,
    lon_right: float,
) -> Tuple[float, float]:
    rel_x = x / image_width if image_width > 0 else 0.0
    rel_y = y / image_height if image_height > 0 else 0.0

    lat = lat_top - rel_y * (lat_top - lat_bottom)
    lon = lon_left + rel_x * (lon_right - lon_left)
    return lat, lon


def compute_image_geo_extent_from_objects(
    objects: List[Dict[str, Any]], image_width: int, image_height: int
) -> Optional[Tuple[float, float, float, float]]:
    if not objects:
        return None

    estimates: List[Tuple[float, float, float, float]] = []

    for obj in objects:
        bbox = obj["bbox"]
        geo_bounds = obj["geo_bounds"]
        x1, y1, x2, y2 = bbox
        lat_top_obj, lon_left_obj, lat_bottom_obj, lon_right_obj = geo_bounds

        if x2 <= x1 or y2 <= y1:
            continue

        # Infer full-image affine extent from this object's pixel+geo box.
        lon_span = lon_right_obj - lon_left_obj
        lat_span = lat_top_obj - lat_bottom_obj

        if lon_span == 0 or lat_span == 0:
            continue

        lon_per_px = lon_span / max(1.0, (x2 - x1))
        lat_per_px = lat_span / max(1.0, (y2 - y1))

        est_lon_left = lon_left_obj - x1 * lon_per_px
        est_lon_right = est_lon_left + image_width * lon_per_px

        est_lat_top = lat_top_obj + y1 * lat_per_px
        est_lat_bottom = est_lat_top - image_height * lat_per_px

        estimates.append((est_lat_top, est_lon_left, est_lat_bottom, est_lon_right))

    if not estimates:
        return None

    arr = np.array(estimates, dtype=np.float64)
    lat_top = float(np.median(arr[:, 0]))
    lon_left = float(np.median(arr[:, 1]))
    lat_bottom = float(np.median(arr[:, 2]))
    lon_right = float(np.median(arr[:, 3]))
    return lat_top, lon_left, lat_bottom, lon_right


def build_chip_metadata(
    image_path: Path,
    image_idx: int,
    objects: List[Dict[str, Any]],
    chips_dir: Path,
    chip_size: int,
    overlap: int,
) -> List[Dict[str, Any]]:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size

    image_extent = compute_image_geo_extent_from_objects(objects, width, height)
    if image_extent is None:
        logger.warning("Skipping %s: unable to infer geo extent", image_path.name)
        return []

    lat_top, lon_left, lat_bottom, lon_right = image_extent

    chips: List[Dict[str, Any]] = []
    stride = max(1, chip_size - overlap)
    chip_idx = 0

    y = 0
    while y < height:
        x = 0
        while x < width:
            x_end = min(x + chip_size, width)
            y_end = min(y + chip_size, height)
            chip_bbox = (x, y, x_end, y_end)

            matched = [obj for obj in objects if intersects(obj["bbox"], chip_bbox)]
            if not matched:
                x += stride
                chip_idx += 1
                continue

            chip = image.crop((x, y, x_end, y_end))
            if chip.size[0] < chip_size or chip.size[1] < chip_size:
                padded = Image.new("RGB", (chip_size, chip_size))
                padded.paste(chip, (0, 0))
                chip = padded

            chip_id = f"xview_{image_idx:06d}_chip_{chip_idx:05d}"
            chip_file = chips_dir / f"{chip_id}.png"
            chip.save(chip_file)

            # Use largest intersecting object as chip anchor bbox.
            best_obj = None
            best_area = -1
            best_rel_bbox = None
            for obj in matched:
                rel_bbox = clip_bbox_to_chip(obj["bbox"], chip_bbox)
                if rel_bbox is None:
                    continue
                rx1, ry1, rx2, ry2 = rel_bbox
                area = (rx2 - rx1) * (ry2 - ry1)
                if area > best_area:
                    best_area = area
                    best_obj = obj
                    best_rel_bbox = rel_bbox

            if best_obj is None or best_rel_bbox is None:
                x += stride
                chip_idx += 1
                continue

            # Geo bounds for the chip from inferred full-image extent.
            chip_lat_top, chip_lon_left = pixel_to_geo_from_image_extent(
                x, y, width, height, lat_top, lon_left, lat_bottom, lon_right
            )
            chip_lat_bottom, chip_lon_right = pixel_to_geo_from_image_extent(
                x_end, y_end, width, height, lat_top, lon_left, lat_bottom, lon_right
            )

            chip_meta = {
                "chip_id": chip_id,
                "image_name": image_path.name,
                "image_idx": image_idx,
                "chip_idx": chip_idx,
                "chip_path": str(chip_file),
                "bbox_pixel": [int(v) for v in best_rel_bbox],
                "image_width": chip_size,
                "image_height": chip_size,
                "lat_top": float(chip_lat_top),
                "lon_left": float(chip_lon_left),
                "lat_bottom": float(chip_lat_bottom),
                "lon_right": float(chip_lon_right),
                "lat_center": float((chip_lat_top + chip_lat_bottom) / 2.0),
                "lon_center": float((chip_lon_left + chip_lon_right) / 2.0),
                "type_id": best_obj.get("type_id"),
                "feature_id": best_obj.get("feature_id"),
            }
            chips.append(chip_meta)

            x += stride
            chip_idx += 1
        y += stride

    return chips


def preprocess_xview_dataset(
    images_dir: Path,
    labels_file: Path,
    output_dir: Path,
    chip_size: int,
    overlap: int,
    max_images: Optional[int],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    chips_dir = output_dir / "chips"
    chips_dir.mkdir(parents=True, exist_ok=True)

    label_index = load_xview_label_index(labels_file)

    image_files = sorted(images_dir.glob("*.tif"))
    if max_images is not None:
        image_files = image_files[:max_images]

    logger.info("Found %d train images", len(image_files))

    all_meta: List[Dict[str, Any]] = []
    used_images = 0

    for img_idx, image_path in enumerate(tqdm(image_files, desc="Preprocessing images")):
        objs = label_index.get(image_path.name, [])
        if not objs:
            continue

        try:
            chip_meta = build_chip_metadata(
                image_path=image_path,
                image_idx=img_idx,
                objects=objs,
                chips_dir=chips_dir,
                chip_size=chip_size,
                overlap=overlap,
            )
            if chip_meta:
                all_meta.extend(chip_meta)
                used_images += 1
        except Exception as exc:
            logger.error("Failed processing %s: %s", image_path.name, exc)

    metadata_file = output_dir / "xview_metadata.json"
    with metadata_file.open("w", encoding="utf-8") as f:
        json.dump(all_meta, f, indent=2)

    logger.info("Preprocess complete")
    logger.info("Images with labels used: %d", used_images)
    logger.info("Chips generated: %d", len(all_meta))
    logger.info("Metadata: %s", metadata_file)
    logger.info("Chips dir: %s", chips_dir)
    return metadata_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess xView train dataset")
    parser.add_argument("--images-dir", type=Path, required=True, help="Path to train_images/train_images")
    parser.add_argument("--labels-file", type=Path, required=True, help="Path to xView_train.geojson")
    parser.add_argument("--output-dir", type=Path, default=Path("./data/metadata"), help="Output metadata dir")
    parser.add_argument("--chip-size", type=int, default=512, help="Chip size in pixels")
    parser.add_argument("--overlap", type=int, default=0, help="Chip overlap in pixels")
    parser.add_argument("--max-images", type=int, default=None, help="Optional limit for quick runs")

    args = parser.parse_args()

    preprocess_xview_dataset(
        images_dir=args.images_dir,
        labels_file=args.labels_file,
        output_dir=args.output_dir,
        chip_size=args.chip_size,
        overlap=args.overlap,
        max_images=args.max_images,
    )


if __name__ == "__main__":
    main()
