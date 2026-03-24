import logging
from typing import List, Tuple
import numpy as np
import cv2
from PIL import Image
import io
from pathlib import Path

logger = logging.getLogger(__name__)


def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """Load image from bytes to numpy array.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Image as numpy array (RGB)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return np.array(image)
    except Exception as e:
        logger.error(f"Failed to load image from bytes: {e}")
        raise ValueError(f"Invalid image format: {e}")


def load_image_from_path(image_path: str) -> np.ndarray:
    """Load image from file path.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Image as numpy array (RGB)
    """
    try:
        image = Image.open(image_path).convert("RGB")
        return np.array(image)
    except Exception as e:
        logger.error(f"Failed to load image from path {image_path}: {e}")
        raise ValueError(f"Cannot load image: {e}")


def resize_image(image: np.ndarray, max_size: Tuple[int, int]) -> np.ndarray:
    """Resize image to fit within max_size while preserving aspect ratio.
    
    Args:
        image: Input image array
        max_size: Maximum (width, height)
        
    Returns:
        Resized image array
    """
    h, w = image.shape[:2]
    max_w, max_h = max_size
    
    if w <= max_w and h <= max_h:
        return image
    
    scale = min(max_w / w, max_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)


def normalize_image_for_clip(image: np.ndarray) -> np.ndarray:
    """Normalize image for CLIP model input.
    
    Args:
        image: Input image array (H, W, 3) in range [0, 255]
        
    Returns:
        Normalized image array
    """
    # Convert to PIL Image, then to tensor via preprocessing
    # CLIP expects PIL Image, will handle normalization internally
    return Image.fromarray(image.astype("uint8"))


def extract_chip(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    padding: int = 0
) -> np.ndarray:
    """Extract a chip/region from image using bbox.
    
    Args:
        image: Input image array
        bbox: (x_min, y_min, x_max, y_max) in pixel coordinates
        padding: Extra padding around bbox
        
    Returns:
        Extracted chip as numpy array
    """
    x_min, y_min, x_max, y_max = bbox
    h, w = image.shape[:2]
    
    # Apply padding
    x_min = max(0, x_min - padding)
    y_min = max(0, y_min - padding)
    x_max = min(w, x_max + padding)
    y_max = min(h, y_max + padding)
    
    return image[y_min:y_max, x_min:x_max]


def create_random_chip(height: int = 512, width: int = 512) -> np.ndarray:
    """Create a random satellite-like image for testing.
    
    Args:
        height: Image height
        width: Image width
        
    Returns:
        Random image array
    """
    # Create a random image with some structure
    image = np.random.randint(50, 200, (height, width, 3), dtype=np.uint8)
    # Add some patterns
    image[100:200, 100:200] = np.random.randint(100, 255, (100, 100, 3), dtype=np.uint8)
    return image


def split_image_into_chips(
    image: np.ndarray,
    chip_size: int = 512,
    overlap: int = 0
) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
    """Split image into overlapping chips.
    
    Args:
        image: Input image array
        chip_size: Size of each chip
        overlap: Overlap between chips in pixels
        
    Returns:
        List of (chip, bbox) tuples
    """
    h, w = image.shape[:2]
    chips = []
    stride = chip_size - overlap
    
    y = 0
    while y < h:
        x = 0
        while x < w:
            x_end = min(x + chip_size, w)
            y_end = min(y + chip_size, h)
            
            # Extract chip
            chip = image[y:y_end, x:x_end]
            
            # Pad if necessary to maintain chip_size
            if chip.shape[0] < chip_size or chip.shape[1] < chip_size:
                chip = cv2.copyMakeBorder(
                    chip,
                    0, chip_size - chip.shape[0],
                    0, chip_size - chip.shape[1],
                    cv2.BORDER_REFLECT
                )
            
            chips.append((chip, (x, y, x_end, y_end)))
            x += stride
        y += stride
    
    return chips


def validate_image_file(file_bytes: bytes, filename: str, max_size: int) -> bool:
    """Validate image file.
    
    Args:
        file_bytes: Image file bytes
        filename: Original filename
        max_size: Maximum allowed file size
        
    Returns:
        True if valid
    """
    # Check file size
    if len(file_bytes) > max_size:
        raise ValueError(f"File size exceeds {max_size} bytes")
    
    # Check format
    ext = Path(filename).suffix.lower().strip(".")
    if ext not in {"jpg", "jpeg", "png", "tiff", "tif", "webp"}:
        raise ValueError(f"Unsupported format: {ext}")
    
    # Try loading
    try:
        Image.open(io.BytesIO(file_bytes)).verify()
        return True
    except Exception as e:
        raise ValueError(f"Invalid image file: {e}")
