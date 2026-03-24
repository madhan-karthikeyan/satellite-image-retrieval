from fastapi import APIRouter, HTTPException
import os
import time
from pathlib import Path

from app.schemas.models import SearchRequest, SearchResponse, SearchResult
from app.services.search import visual_search_service
from app.core.config import settings

router = APIRouter()


@router.post("/execute", response_model=SearchResponse)
async def execute_search(request: SearchRequest):
    start_time = time.time()
    
    if not os.path.exists(request.target_directory):
        raise HTTPException(status_code=404, detail=f"Target directory not found: {request.target_directory}")
    
    try:
        results = visual_search_service.search_in_imagery(
            target_directory=request.target_directory,
            object_name=request.object_name,
            similarity_threshold=request.similarity_threshold,
            max_results=settings.MAX_RESULTS
        )
        
        output_file = None
        if results:
            output_path = os.path.join(
                request.output_directory,
                f"GC_PS03_search_results"
            )
            output_file = visual_search_service.save_results_to_file(
                results=results,
                output_path=output_path,
                batch_name=request.batch_name or "team"
            )
        
        processing_time = time.time() - start_time
        
        search_results = [
            SearchResult(
                x_min=r["x_min"],
                y_min=r["y_min"],
                x_max=r["x_max"],
                y_max=r["y_max"],
                searched_object_name=r["searched_object_name"],
                target_imagery_file_name=r["target_imagery_file_name"],
                similarity_score=r["similarity_score"]
            )
            for r in results
        ]
        
        return SearchResponse(
            success=True,
            message=f"Search completed successfully. Found {len(results)} matches.",
            results_count=len(results),
            results=search_results,
            output_file=output_file,
            processing_time_seconds=round(processing_time, 2)
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        return SearchResponse(
            success=False,
            message=f"Search failed: {str(e)}",
            results_count=0,
            results=[],
            output_file=None,
            processing_time_seconds=round(processing_time, 2)
        )


@router.post("/batch")
async def batch_search(
    searches: list[SearchRequest]
):
    all_results = []
    output_files = []
    start_time = time.time()
    
    for search_req in searches:
        try:
            results = visual_search_service.search_in_imagery(
                target_directory=search_req.target_directory,
                object_name=search_req.object_name,
                similarity_threshold=search_req.similarity_threshold,
                max_results=settings.MAX_RESULTS
            )
            
            output_path = os.path.join(
                search_req.output_directory,
                f"GC_PS03_{search_req.object_name}_results"
            )
            output_file = visual_search_service.save_results_to_file(
                results=results,
                output_path=output_path,
                batch_name=search_req.batch_name or "team"
            )
            
            all_results.extend(results)
            output_files.append(output_file)
        except Exception as e:
            print(f"Error in batch search for {search_req.object_name}: {e}")
    
    processing_time = time.time() - start_time
    
    return {
        "success": True,
        "message": f"Batch search completed. Found {len(all_results)} total matches.",
        "total_results": len(all_results),
        "results_by_object": {req.object_name: sum(1 for r in all_results if r["searched_object_name"] == req.object_name) for req in searches},
        "output_files": output_files,
        "processing_time_seconds": round(processing_time, 2)
    }


@router.get("/results/{output_filename}")
async def get_saved_results(
    output_filename: str,
    directory: str
):
    file_path = Path(directory) / output_filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Results file not found")
    
    with open(file_path, "r") as f:
        content = f.read()
    
    results = []
    for line in content.strip().split("\n"):
        if line:
            parts = line.split()
            if len(parts) >= 7:
                results.append({
                    "x_min": int(parts[0]),
                    "y_min": int(parts[1]),
                    "x_max": int(parts[2]),
                    "y_max": int(parts[3]),
                    "searched_object_name": parts[4],
                    "target_imagery_file_name": parts[5],
                    "similarity_score": float(parts[6])
                })
    
    return {
        "success": True,
        "filename": output_filename,
        "total_results": len(results),
        "results": results
    }


@router.get("/status")
async def get_search_status():
    from app.services.chroma import chroma_service
    
    return {
        "status": "ready",
        "available_objects": chroma_service.list_object_names(),
        "total_chips": chroma_service.count_chips(),
        "search_threshold": settings.SEARCH_THRESHOLD,
        "sliding_window_sizes": visual_search_service.sliding_window_sizes,
        "stride": visual_search_service.stride
    }
