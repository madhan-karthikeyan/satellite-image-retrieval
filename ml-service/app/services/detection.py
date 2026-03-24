import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    bbox: List[int]
    score: float
    label: str
    label_id: int
    center: Tuple[float, float]


class DetectionService:
    """Lightweight detection/refinement service for satellite chips.

    This provides a production-safe baseline detector using CV heuristics
    (saliency-like thresholding + contour proposals). It can be replaced
    by YOLO/other detectors without changing API contracts.
    """

    def __init__(
        self,
        score_threshold: float = 0.4,
        max_boxes: int = 20,
    ):
        self.score_threshold = score_threshold
        self.max_boxes = max_boxes

    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect candidate objects in a satellite image.

        Returns:
            List of detections with bbox, score, label, center
        """
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]
        if h < 8 or w < 8:
            return []

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Adaptive threshold to pick structures/buildings/vehicles-like blobs.
        thr = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            -8,
        )

        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(thr, cv2.MORPH_OPEN, kernel, iterations=1)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=1)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates: List[DetectionResult] = []
        image_area = float(h * w)

        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            area = float(bw * bh)
            if area < 16 or area > 0.5 * image_area:
                continue

            aspect = bw / max(1.0, float(bh))
            if aspect < 0.15 or aspect > 8.0:
                continue

            roi = gray[y : y + bh, x : x + bw]
            if roi.size == 0:
                continue

            contrast = float(np.std(roi)) / 64.0
            compactness = float(cv2.contourArea(cnt)) / max(1.0, area)
            area_ratio = area / image_area

            raw_score = 0.5 * min(1.0, contrast) + 0.35 * min(1.0, compactness) + 0.15 * min(1.0, area_ratio * 25)
            score = float(max(0.0, min(1.0, raw_score)))

            if score < self.score_threshold:
                continue

            x2 = x + bw
            y2 = y + bh
            cx = x + bw / 2.0
            cy = y + bh / 2.0

            candidates.append(
                DetectionResult(
                    bbox=[int(x), int(y), int(x2), int(y2)],
                    score=score,
                    label="object",
                    label_id=0,
                    center=(cx, cy),
                )
            )

        candidates.sort(key=lambda d: d.score, reverse=True)
        candidates = candidates[: self.max_boxes]

        return [
            {
                "bbox": d.bbox,
                "score": d.score,
                "label": d.label,
                "label_id": d.label_id,
                "center": [float(d.center[0]), float(d.center[1])],
            }
            for d in candidates
        ]

    def best_detection(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        detections = self.detect(image)
        return detections[0] if detections else None
