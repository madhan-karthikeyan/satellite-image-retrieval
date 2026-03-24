from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os
import cv2
import numpy as np
from typing import List, Optional

from app.schemas.models import ImageryListResponse, ImageryInfo
from app.core.config import settings

router = APIRouter()


def get_imagery_info(file_path: str) -> Optional[ImageryInfo]:
    try:
        img = cv2.imread(file_path)
        if img is not None:
            return ImageryInfo(
                filename=os.path.basename(file_path),
                width=img.shape[1],
                height=img.shape[0],
                bands=img.shape[2] if len(img.shape) == 3 else 1,
                format=file_path.split('.')[-1].upper()
            )
        
        try:
            import rasterio
            with rasterio.open(file_path) as src:
                return ImageryInfo(
                    filename=os.path.basename(file_path),
                    width=src.width,
                    height=src.height,
                    bands=src.count,
                    format="TIFF"
                )
        except:
            pass
        
        return None
    except:
        return None


@router.get("/list")
async def list_imagery(directory: str):
    if not os.path.exists(directory):
        raise HTTPException(status_code=404, detail=f"Directory not found: {directory}")
    
    imagery_list = []
    for ext in ["*.tif", "*.tiff", "*.png", "*.jpg", "*.jpeg"]:
        for file_path in Path(directory).glob(ext):
            info = get_imagery_info(str(file_path))
            if info:
                imagery_list.append(info)
        for file_path in Path(directory).glob(ext.upper()):
            info = get_imagery_info(str(file_path))
            if info:
                imagery_list.append(info)
    
    return ImageryListResponse(
        success=True,
        imagery_count=len(imagery_list),
        imagery_list=imagery_list
    )


@router.get("/preview/{filename}")
async def get_imagery_preview(
    filename: str,
    directory: str
):
    file_path = Path(directory) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    try:
        img = cv2.imread(str(file_path))
        if img is None:
            try:
                import rasterio
                with rasterio.open(str(file_path)) as src:
                    data = src.read([1, 2, 3])
                    data = np.transpose(data, (1, 2, 0))
                    data = data.astype(np.float32)
                    for i in range(data.shape[2]):
                        band = data[:, :, i]
                        p2, p98 = np.percentile(band, (2, 98))
                        if p98 > p2:
                            band = np.clip((band - p2) / (p98 - p2), 0, 1)
                        data[:, :, i] = band
                    img = (data[:, :, :3] * 255).astype(np.uint8)
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Could not read image: {str(e)}")
        
        preview_path = settings.UPLOAD_DIR / f"preview_{filename}.jpg"
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        cv2.imwrite(str(preview_path), img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        return FileResponse(str(preview_path), media_type="image/jpeg")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")


@router.get("/tile")
async def get_tile(
    directory: str,
    filename: str,
    x: int,
    y: int,
    size: int = 256
):
    file_path = Path(directory) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    try:
        img = cv2.imread(str(file_path))
        if img is None:
            try:
                import rasterio
                with rasterio.open(str(file_path)) as src:
                    data = src.read([1, 2, 3])
                    data = np.transpose(data, (1, 2, 0))
                    data = data.astype(np.float32)
                    for i in range(data.shape[2]):
                        band = data[:, :, i]
                        p2, p98 = np.percentile(band, (2, 98))
                        if p98 > p2:
                            band = np.clip((band - p2) / (p98 - p2), 0, 1)
                        data[:, :, i] = band
                    img = (data[:, :, :3] * 255).astype(np.uint8)
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            except:
                raise HTTPException(status_code=500, detail="Could not read image")
        
        h, w = img.shape[:2]
        
        x1 = max(0, x * size)
        y1 = max(0, y * size)
        x2 = min(w, x1 + size)
        y2 = min(h, y1 + size)
        
        tile = img[y1:y2, x1:x2]
        
        tile_path = settings.UPLOAD_DIR / f"tile_{filename}_{x}_{y}.jpg"
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        cv2.imwrite(str(tile_path), tile, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        return FileResponse(str(tile_path), media_type="image/jpeg")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating tile: {str(e)}")
