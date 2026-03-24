#!/usr/bin/env python3
"""
Example client for testing the satellite search API.

Usage:
    python example_client.py --image test.jpg --top-k 10
"""

import argparse
import requests
import json
from pathlib import Path
from typing import List, Dict, Any
import sys


class SatelliteSearchClient:
    """Client for satellite image search API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize client.
        
        Args:
            base_url: API base URL
        """
        self.base_url = base_url
    
    def health_check(self) -> bool:
        """Check API health."""
        try:
            response = requests.get(f"{self.base_url}/health")
            status = response.json()
            print("✓ API Health Check:")
            print(f"  Status: {status['status']}")
            print(f"  Total Embeddings: {status['index_status']['total_embeddings']}")
            return True
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return False
    
    def search_image(
        self,
        image_path: str,
        top_k: int = 10,
        threshold: float = 0.3
    ) -> Dict[str, Any]:
        """Search for similar images.
        
        Args:
            image_path: Path to query image
            top_k: Number of top results
            threshold: Minimum similarity
            
        Returns:
            Search results
        """
        with open(image_path, 'rb') as f:
            files = {'image': f}
            params = {'top_k': top_k, 'threshold': threshold}
            response = requests.post(
                f"{self.base_url}/api/search",
                files=files,
                params=params
            )
        
        return response.json()
    
    def export_results_txt(
        self,
        image_path: str,
        output_path: str,
        top_k: int = 10
    ) -> None:
        """Export results as TXT.
        
        Args:
            image_path: Path to query image
            output_path: Output file path
            top_k: Number of results
        """
        with open(image_path, 'rb') as f:
            files = {'image': f}
            params = {'top_k': top_k}
            response = requests.post(
                f"{self.base_url}/api/search/export-txt",
                files=files,
                params=params
            )
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Exported results to {output_path}")
    
    def export_results_json(
        self,
        image_path: str,
        output_path: str,
        top_k: int = 10
    ) -> None:
        """Export results as JSON.
        
        Args:
            image_path: Path to query image
            output_path: Output file path
            top_k: Number of results
        """
        with open(image_path, 'rb') as f:
            files = {'image': f}
            params = {'top_k': top_k}
            response = requests.post(
                f"{self.base_url}/api/search/export-json",
                files=files,
                params=params
            )
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Exported results to {output_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics.
        
        Returns:
            Statistics
        """
        response = requests.get(f"{self.base_url}/api/search/stats")
        return response.json()
    
    def get_index_status(self) -> Dict[str, Any]:
        """Get index status.
        
        Returns:
            Index status
        """
        response = requests.get(f"{self.base_url}/api/index/status")
        return response.json()
    
    def build_index(self) -> Dict[str, Any]:
        """Trigger index build.
        
        Returns:
            Build status
        """
        response = requests.post(f"{self.base_url}/api/index/build")
        return response.json()
    
    def reset_index(self) -> Dict[str, Any]:
        """Reset index.
        
        Returns:
            Reset status
        """
        response = requests.post(f"{self.base_url}/api/index/reset")
        return response.json()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Satellite search client")
    parser.add_argument("--image", type=str, help="Image file to search")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    parser.add_argument("--threshold", type=float, default=0.3, help="Similarity threshold")
    parser.add_argument("--export-txt", type=str, help="Export results as TXT")
    parser.add_argument("--export-json", type=str, help="Export results as JSON")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--status", action="store_true", help="Show index status")
    parser.add_argument("--health", action="store_true", help="Health check")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="API URL")
    
    args = parser.parse_args()
    
    client = SatelliteSearchClient(base_url=args.url)
    
    # Health check
    if args.health:
        client.health_check()
        return
    
    # Stats
    if args.stats:
        stats = client.get_stats()
        print("✓ Service Statistics:")
        print(json.dumps(stats, indent=2))
        return
    
    # Index status
    if args.status:
        status = client.get_index_status()
        print("✓ Index Status:")
        print(json.dumps(status, indent=2))
        return
    
    # Search
    if args.image:
        if not Path(args.image).exists():
            print(f"✗ Image file not found: {args.image}")
            sys.exit(1)
        
        print(f"Searching for similar images...")
        results = client.search_image(args.image, top_k=args.top_k, threshold=args.threshold)
        
        if results['success']:
            print(f"✓ Found {results['count']} results (search time: {results['search_time_ms']:.1f}ms)")
            print("\nResults:")
            for i, result in enumerate(results['results'], 1):
                print(f"{i}. {result['chip_id']}")
                print(f"   Location: {result['lat']:.4f}, {result['lon']:.4f}")
                print(f"   Score: {result['score']:.3f}")
                print(f"   Image: {result['image_name']}")
        else:
            print(f"✗ Search failed: {results}")
        
        # Export if requested
        if args.export_txt:
            client.export_results_txt(args.image, args.export_txt, top_k=args.top_k)
        
        if args.export_json:
            client.export_results_json(args.image, args.export_json, top_k=args.top_k)


if __name__ == "__main__":
    main()
