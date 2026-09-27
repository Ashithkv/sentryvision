import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.detection.yolo_detector import YoloDetector
from app.services.detection_service import get_detector, manager, state

logger = logging.getLogger("sentryvision.ws")
router = APIRouter()


@router.websocket("/ws/detection")
async def websocket_detection(websocket: WebSocket):
    await manager.connect(websocket)

    # Send the client the current config + available classes immediately
    # so the UI can populate its object-selector dropdown.
    detector: YoloDetector = get_detector()
    await websocket.send_json({
        "type": "init",
        "confidence_threshold": state.confidence_threshold,
        "roi": [state.roi.x1, state.roi.y1, state.roi.x2, state.roi.y2],
        "watched_classes": list(state.watched_classes),
        "available_classes": detector.available_classes(),
    })

    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") == "config":
                state.apply_config(payload)
                await websocket.send_json({"type": "config_ack", "ok": True})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:  # malformed message, etc — don't kill the server
        logger.warning("WebSocket error: %s", exc)
        manager.disconnect(websocket)
