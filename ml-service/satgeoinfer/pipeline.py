"""Main inference pipeline for satellite geolocation with improved accuracy."""

import os
from typing import Optional
from PIL import Image
import torch
from openai import OpenAI

from .embedder import Embedder
from .retriever import Retriever
from .confidence import geographic_inference


class SatGeoInfer:
    """Satellite geolocation inference system with TTA and ensemble support."""

    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        retriever: Optional[Retriever] = None,
        use_tta: bool = True,
        use_ensemble: bool = True,
        use_multiscale: bool = False
    ):
        """Initialize the inference pipeline.
        
        Args:
            embedder: Custom embedder instance (None for default with TTA)
            retriever: Custom retriever instance (None for default with ensemble)
            use_tta: Enable Test-Time Augmentation for more robust embeddings
            use_ensemble: Enable ensemble retrieval for better accuracy
            use_multiscale: Enable multi-scale embedding for varied image sizes
        """
        self.use_tta = use_tta
        self.use_ensemble = use_ensemble
        self.use_multiscale = use_multiscale
        
        if embedder is None:
            self.embedder = Embedder(use_tta=use_tta, tta_augmentations=8)
        else:
            self.embedder = embedder
            
        if retriever is None:
            self.retriever = Retriever(ensemble_strategy="rrf")
        else:
            self.retriever = retriever
            
        self._openai_client = None

    @property
    def openai_client(self) -> Optional[OpenAI]:
        """Lazy initialization of OpenRouter client."""
        if self._openai_client is None:
            api_key = os.getenv("OPENROUTER_KEY")
            if api_key:
                self._openai_client = OpenAI(
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
        return self._openai_client

    def infer(
        self,
        image_path: str,
        explain: bool = False,
        use_tta: Optional[bool] = None,
        use_ensemble: Optional[bool] = None
    ) -> dict:
        """Perform geolocation inference on an image.
        
        Args:
            image_path: Path to image file
            explain: Generate natural language explanation
            use_tta: Override TTA setting for this inference
            use_ensemble: Override ensemble setting for this inference
            
        Returns:
            Inference result dictionary
        """
        image = Image.open(image_path).convert("RGB")
        return self.infer_from_image(
            image,
            explain=explain,
            use_tta=use_tta,
            use_ensemble=use_ensemble
        )

    def infer_from_image(
        self,
        image: Image.Image,
        explain: bool = False,
        use_tta: Optional[bool] = None,
        use_ensemble: Optional[bool] = None,
        second_stage: bool = False
    ) -> dict:
        """Perform geolocation inference from a PIL Image.
        
        Args:
            image: PIL Image
            explain: Generate natural language explanation
            use_tta: Override TTA setting for this inference
            use_ensemble: Override ensemble setting for this inference
            second_stage: Enable second-stage clustering refinement
            
        Returns:
            Inference result dictionary with location, confidence, and metadata
        """
        effective_tta = use_tta if use_tta is not None else self.use_tta
        effective_ensemble = use_ensemble if use_ensemble is not None else self.use_ensemble
        
        if effective_tta:
            embedding = self.embedder.embed_with_tta(image)
        elif self.use_multiscale:
            embedding = self.embedder.embed_image_multiscale(image)
        else:
            embedding = self.embedder.embed_image(image)

        candidates = self.retriever.retrieve(
            query_embedding=embedding,
            top_k=100,
            sim_threshold=0.65,
            use_ensemble=effective_ensemble
        )

        result = geographic_inference(candidates)

        if second_stage and result:
            result = self._apply_second_stage(image, embedding, result)

        if result is None:
            return {
                "status": "insufficient_confidence",
                "message": "Insufficient candidates for reliable inference",
                "candidates_retrieved": len(candidates)
            }

        if explain:
            explanation = self._generate_explanation(result)
            result["explanation"] = explanation

        result["status"] = "success"
        result["inference_metadata"] = {
            "use_tta": effective_tta,
            "use_ensemble": effective_ensemble,
            "embedding_dim": len(embedding)
        }
        
        return result

    def infer_with_confidence_bands(
        self,
        image: Image.Image
    ) -> dict:
        """Perform inference with multiple confidence bands.
        
        Returns results at different confidence thresholds for flexibility.
        
        Args:
            image: PIL Image
            
        Returns:
            Dictionary with multiple result sets at different thresholds
        """
        embedding = self.embedder.embed_with_tta(image)
        
        results = {
            "high_confidence": None,
            "medium_confidence": None,
            "low_confidence": None,
            "all_candidates": None
        }
        
        for threshold, key in [(0.70, "high_confidence"), (0.55, "medium_confidence"), (0.40, "low_confidence")]:
            candidates = self.retriever.retrieve(
                query_embedding=embedding,
                top_k=100,
                sim_threshold=threshold,
                use_ensemble=False
            )
            result = geographic_inference(candidates)
            results[key] = result
        
        candidates = self.retriever.retrieve(
            query_embedding=embedding,
            top_k=200,
            sim_threshold=0.30,
            use_ensemble=True
        )
        results["all_candidates"] = geographic_inference(candidates)
        
        return results

    def _generate_explanation(self, result: dict) -> Optional[str]:
        """Generate natural language explanation."""
        if self.openai_client is None:
            return self._generate_rule_based_explanation(result)

        try:
            prompt = self._build_explanation_prompt(result)
            response = self.openai_client.chat.completions.create(
                model="meta-llama/llama-3-8b-instruct",
                messages=[
                    {"role": "system", "content": "You are a concise assistant that provides brief geographic inference summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            return response.choices[0].message.content
        except Exception:
            return self._generate_rule_based_explanation(result)

    def _generate_rule_based_explanation(self, result: dict) -> str:
        """Generate deterministic rule-based explanation."""
        lat = result.get("centroid_lat", 0)
        lon = result.get("centroid_lon", 0)
        confidence = result.get("confidence_level", "unknown")
        confidence_score = result.get("confidence_score", 0)
        radius = result.get("confidence_radius_km", 0)
        cluster_size = result.get("cluster_size", 0)

        scene_info = ""
        if result.get("scene_distribution"):
            scenes = result["scene_distribution"]
            top_scenes = sorted(scenes.items(), key=lambda x: x[1], reverse=True)[:3]
            scene_info = f" Dominant scene types: {', '.join([s for s, _ in top_scenes])}"

        return (
            f"Predicted location at {lat:.4f}, {lon:.4f} with {confidence.upper()} "
            f"confidence (score: {confidence_score:.2f}, radius ~{radius:.0f}km, "
            f"{cluster_size} matching images).{scene_info}"
        )

    def _build_explanation_prompt(self, result: dict) -> str:
        """Build prompt for explanation generation."""
        scene_info = ""
        if result.get("scene_distribution"):
            scenes = result["scene_distribution"]
            top_scenes = sorted(scenes.items(), key=lambda x: x[1], reverse=True)[:3]
            scene_info = f"Top scene types: {', '.join([f'{s}({c})' for s, c in top_scenes])}"

        return f"""Given this geolocation result:
- Predicted location: {result['centroid_lat']:.4f}, {result['centroid_lon']:.4f}
- Confidence level: {result['confidence_level']} (score: {result.get('confidence_score', 0):.2f}, radius: {result['confidence_radius_km']:.0f}km)
- Cluster size: {result['cluster_size']} images
- {scene_info}

Provide a strict 2-3 sentence summary."""

    def _apply_second_stage(
        self,
        image: Image.Image,
        embedding: torch.Tensor,
        initial_result: dict
    ) -> dict:
        """Apply second-stage clustering refinement.
        
        Re-queries with tighter geographic constraints around initial prediction.
        """
        import numpy as np
        
        center_lat = initial_result.get("centroid_lat", 0)
        center_lon = initial_result.get("centroid_lon", 0)
        
        refined_candidates = self.retriever.retrieve(
            query_embedding=embedding,
            top_k=200,
            sim_threshold=0.70,
            use_ensemble=True
        )
        
        if len(refined_candidates) < 5:
            return initial_result
            
        lats = [c["lat"] for c in refined_candidates]
        lons = [c["lon"] for c in refined_candidates]
        
        median_lat = float(np.median(lats))
        median_lon = float(np.median(lons))
        
        lat_std = float(np.std(lats)) if len(lats) > 1 else 1.0
        lon_std = float(np.std(lons)) if len(lons) > 1 else 1.0
        
        from .confidence import compute_confidence_radius
        radius_km = compute_confidence_radius(lat_std, lon_std, median_lat)
        
        initial_result["centroid_lat"] = median_lat
        initial_result["centroid_lon"] = median_lon
        initial_result["confidence_radius_km"] = radius_km
        initial_result["second_stage_refined"] = True
        
        return initial_result


def create_pipeline(
    embedder: Optional[Embedder] = None,
    retriever: Optional[Retriever] = None,
    use_tta: bool = True,
    use_ensemble: bool = True
) -> SatGeoInfer:
    """Factory function to create a pipeline instance."""
    return SatGeoInfer(
        embedder=embedder,
        retriever=retriever,
        use_tta=use_tta,
        use_ensemble=use_ensemble
    )
