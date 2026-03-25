"""Evaluation script for satellite geolocation accuracy metrics."""

import argparse
import sys
import json
import time
from pathlib import Path
from typing import Optional
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from datasets import load_dataset
from tqdm import tqdm
from haversine import haversine

from satgeoinfer.embedder import Embedder
from satgeoinfer.retriever import Retriever
from satgeoinfer.pipeline import SatGeoInfer
from satgeoinfer.confidence import geographic_inference


def compute_geolocation_error(pred_lat: float, pred_lon: float, true_lat: float, true_lon: float) -> float:
    """Compute haversine distance between predicted and true location."""
    return haversine((pred_lat, pred_lon), (true_lat, true_lon))


def compute_accuracy_at_threshold(errors: list[float], threshold_km: float) -> float:
    """Compute accuracy (fraction of predictions within threshold)."""
    if not errors:
        return 0.0
    return sum(1 for e in errors if e <= threshold_km) / len(errors)


def compute_median_error(errors: list[float]) -> float:
    """Compute median geolocation error."""
    if not errors:
        return float('inf')
    return float(np.median(errors))


def compute_mean_error(errors: list[float]) -> float:
    """Compute mean geolocation error."""
    if not errors:
        return float('inf')
    return float(np.mean(errors))


def compute_percentile_error(errors: list[float], percentile: float) -> float:
    """Compute percentile of geolocation errors."""
    if not errors:
        return float('inf')
    return float(np.percentile(errors, percentile))


def evaluate_pipeline(
    pipeline: SatGeoInfer,
    dataset,
    sample_size: Optional[int] = None,
    exclude_ids: set = None
) -> dict:
    """Evaluate pipeline on dataset.
    
    Args:
        pipeline: SatGeoInfer pipeline instance
        dataset: HuggingFace dataset
        sample_size: Number of samples to evaluate (None for all)
        exclude_ids: Set of image IDs to exclude (e.g., training data)
        
    Returns:
        Dictionary of evaluation metrics
    """
    errors = []
    confidence_correct = defaultdict(list)
    confidence_counts = defaultdict(int)
    scene_errors = defaultdict(list)
    scene_counts = defaultdict(int)
    
    indices = range(len(dataset))
    if sample_size:
        indices = indices[:sample_size]
    
    print(f"Evaluating {len(list(indices))} samples...")
    
    for i in tqdm(indices, desc="Evaluating"):
        example = dataset[i]
        image_id = example.get('image_id', f"test_{i}")
        
        if exclude_ids and image_id in exclude_ids:
            continue
        
        true_lat = example['lat']
        true_lon = example['lon']
        
        try:
            result = pipeline.infer_from_image(example['image'])
            
            if result['status'] == 'success':
                pred_lat = result['centroid_lat']
                pred_lon = result['centroid_lon']
                error = compute_geolocation_error(pred_lat, pred_lon, true_lat, true_lon)
                errors.append(error)
                
                confidence = result['confidence_level']
                confidence_counts[confidence] += 1
                
                if error <= 100:
                    confidence_correct[confidence].append(1)
                else:
                    confidence_correct[confidence].append(0)
                
                scene = example.get('category', example.get('label', 'unknown'))
                scene_counts[scene] += 1
                scene_errors[scene].append(error)
                
        except Exception as e:
            continue
    
    if not errors:
        return {
            "status": "no_valid_predictions",
            "num_samples": len(list(indices))
        }
    
    thresholds = [25, 50, 100, 200, 500, 1000]
    accuracy_at_threshold = {
        f"acc@{t}km": compute_accuracy_at_threshold(errors, t)
        for t in thresholds
    }
    
    metrics = {
        "num_predictions": len(errors),
        "mean_error_km": compute_mean_error(errors),
        "median_error_km": compute_median_error(errors),
        "p75_error_km": compute_percentile_error(errors, 75),
        "p90_error_km": compute_percentile_error(errors, 90),
        "p95_error_km": compute_percentile_error(errors, 95),
        **accuracy_at_threshold
    }
    
    confidence_accuracy = {}
    for conf, correct in confidence_correct.items():
        if correct:
            confidence_accuracy[f"acc@{conf}"] = sum(correct) / len(correct)
    metrics["confidence_accuracy"] = confidence_accuracy
    
    metrics["confidence_distribution"] = dict(confidence_counts)
    
    if len(scene_errors) > 0:
        scene_metrics = {
            scene: {
                "count": scene_counts[scene],
                "mean_error_km": compute_mean_error(errs),
                "median_error_km": compute_median_error(errs)
            }
            for scene, errs in scene_errors.items()
            if scene_counts[scene] >= 5
        }
        metrics["scene_metrics"] = scene_metrics
    
    return metrics


def compare_strategies(
    dataset,
    sample_size: int = 100,
    exclude_ids: set = None
) -> dict:
    """Compare different inference strategies.
    
    Args:
        dataset: HuggingFace dataset
        sample_size: Number of samples to evaluate
        exclude_ids: Set of image IDs to exclude
        
    Returns:
        Dictionary comparing strategies
    """
    strategies = {
        "baseline": {"use_tta": False, "use_ensemble": False},
        "tta_only": {"use_tta": True, "use_ensemble": False},
        "ensemble_only": {"use_tta": False, "use_ensemble": True},
        "tta_ensemble": {"use_tta": True, "use_ensemble": True},
    }
    
    results = {}
    
    for name, config in strategies.items():
        print(f"\nEvaluating {name}...")
        pipeline = SatGeoInfer(
            use_tta=config["use_tta"],
            use_ensemble=config["use_ensemble"]
        )
        
        start_time = time.time()
        metrics = evaluate_pipeline(pipeline, dataset, sample_size, exclude_ids)
        elapsed = time.time() - start_time
        
        metrics["time_per_sample_ms"] = (elapsed / sample_size) * 1000
        results[name] = metrics
        
        print(f"  Median error: {metrics.get('median_error_km', 'N/A'):.1f} km")
        print(f"  Accuracy@100km: {metrics.get('acc@100km', 0):.2%}")
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Evaluate satellite geolocation accuracy")
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        choices=["train", "val", "test"],
        help="Dataset split to evaluate on"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=500,
        help="Number of samples to evaluate"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare different inference strategies"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file for results"
    )
    
    args = parser.parse_args()
    
    print(f"Loading {args.split} dataset...")
    dataset = load_dataset(
        "danielz01/fMoW",
        split=args.split,
        cache_dir="./data/fmow"
    )
    
    if args.compare:
        results = compare_strategies(
            dataset,
            sample_size=args.sample_size
        )
    else:
        pipeline = SatGeoInfer(use_tta=True, use_ensemble=True)
        results = evaluate_pipeline(
            pipeline,
            dataset,
            sample_size=args.sample_size
        )
    
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(json.dumps(results, indent=2))
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
