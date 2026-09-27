from fastapi import APIRouter, Query

from app.database import clear_detections, list_detections

router = APIRouter()


@router.get("/detections")
def get_detections(limit: int = Query(200, ge=1, le=1000),
                    only_roi: bool = Query(False)):
    """Most recent detection events, newest first."""
    return {"detections": list_detections(limit=limit, only_roi=only_roi)}


@router.delete("/detections")
def delete_detections():
    """Clear detection history (used by the 'Clear history' button)."""
    deleted = clear_detections()
    return {"deleted": deleted}
