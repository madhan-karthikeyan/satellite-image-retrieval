from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os
import shutil
from datetime import datetime

from app.schemas.models import ChipUploadResponse, ImageChipInfo
from app.services.search import visual_search_service
from app.core.config import settings

router = APIRouter()


@router.post("/chip", response_model=ChipUploadResponse)
async def upload_chip(
    file: UploadFile = File(...),
    object_name: str = Form(...)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = settings.UPLOAD_DIR / safe_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    try:
        chip_id, metadata = visual_search_service.process_uploaded_chip(
            str(file_path),
            object_name
        )
        
        chip_info = ImageChipInfo(
            id=chip_id,
            filename=metadata["filename"],
            object_name=metadata["object_name"],
            width=metadata["width"],
            height=metadata["height"],
            channels=metadata["channels"],
            uploaded_at=datetime.fromisoformat(metadata["uploaded_at"])
        )
        
        return ChipUploadResponse(
            success=True,
            message=f"Chip uploaded and embedded successfully",
            chip_id=chip_id,
            chip_info=chip_info
        )
    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process chip: {str(e)}")


@router.post("/chip-from-box")
async def upload_chip_from_box(
    file: UploadFile = File(...),
    object_name: str = Form(...),
    x_min: int = Form(...),
    y_min: int = Form(...),
    x_max: int = Form(...),
    y_max: int = Form(...)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = settings.UPLOAD_DIR / safe_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    try:
        chip_id, metadata = visual_search_service.process_drawn_box(
            str(file_path),
            (x_min, y_min, x_max, y_max),
            object_name
        )
        
        return {
            "success": True,
            "message": "Chip extracted from box and embedded successfully",
            "chip_id": chip_id,
            "bbox": {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max}
        }
    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process chip: {str(e)}")


@router.get("/chips")
async def list_chips():
    from app.services.chroma import chroma_service
    object_names = chroma_service.list_object_names()
    
    chips_info = []
    for obj_name in object_names:
        count = chroma_service.count_chips(obj_name)
        chips_info.append({
            "object_name": obj_name,
            "count": count
        })
    
    return {
        "success": True,
        "total_chips": chroma_service.count_chips(),
        "chips": chips_info
    }


@router.delete("/chips/{object_name}")
async def delete_chips(object_name: str):
    success = visual_search_service.chroma_service.delete_by_object_name(object_name)
    
    return {
        "success": success,
        "message": f"Deleted all chips for object '{object_name}'" if success else "Failed to delete chips"
    }
