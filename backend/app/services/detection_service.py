"""
Ties the other pieces together into one continuous loop:

    camera frame -> YOLO detection -> ROI check -> draw overlay
                  -> JPEG encode -> broadcast over WebSocket
                  -> persist to SQLite -> raise alerts

Design choice: there is a single shared detection loop (one camera,
one model instance), not one loop per WebSocket client. Every
connected browser tab just receives a copy of the same stream. This
matches the "don't build a distributed platform" brief — a real
multi-camera / multi-tenant system would need a very different
architecture, but that's explicitly out of scope here.
"""

import asyncio
import base64
import logging
import time

import cv2

from app.config import settings
from app.database import insert_detection
from app.detection.roi import ROI, box_center
from app.detection.yolo_detector import YoloDetector
from app.services.alert_service import evaluate_alerts
from app.services.camera_service import CameraService

logger = logging.getLogger("sentryvision.pipeline")

BOX_COLOR = (0, 217, 163)       # BGR - normal detection
ROI_HIT_COLOR = (0, 91, 255)    # BGR - detection inside ROI (alert-colored)
ROI_BORDER_COLOR = (255, 200, 0)


class StreamState:
    """Mutable, shared configuration that any connected client can update."""

    def __init__(self):
        self.confidence_threshold = settings.DEFAULT_CONFIDENCE_THRESHOLD
        self.roi = ROI.from_tuple(settings.DEFAULT_ROI)
        self.watched_classes: set[str] = set(settings.DEFAULT_ALERT_CLASSES)
        self.running = False

    def apply_config(self, payload: dict) -> None:
        if "confidence" in payload:
            self.confidence_threshold = max(0.05, min(0.95, float(payload["confidence"])))
        if "roi" in payload and payload["roi"]:
            self.roi = ROI.from_tuple(tuple(payload["roi"]))
        if "watched_classes" in payload and payload["watched_classes"] is not None:
            self.watched_classes = set(payload["watched_classes"])


class ConnectionManager:
    def __init__(self):
        self.active: list = []

    async def connect(self, websocket):
        await websocket.accept()
        self.active.append(websocket)
        logger.info("Client connected (%d active)", len(self.active))

    def disconnect(self, websocket):
        if websocket in self.active:
            self.active.remove(websocket)
        logger.info("Client disconnected (%d active)", len(self.active))

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()
state = StreamState()
_detector: YoloDetector | None = None
_camera: CameraService | None = None


def get_detector() -> YoloDetector:
    global _detector
    if _detector is None:
        _detector = YoloDetector()
    return _detector


def get_camera() -> CameraService:
    global _camera
    if _camera is None:
        _camera = CameraService()
    return _camera


def _encode_frame_to_data_url(frame) -> str:
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    if not ok:
        return ""
    b64 = base64.b64encode(buffer).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _draw_overlay(frame, detections: list[dict], roi: ROI):
    h, w = frame.shape[:2]

    rx1, ry1, rx2, ry2 = roi.to_pixels(w, h)
    cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), ROI_BORDER_COLOR, 2)
    cv2.putText(frame, "ROI", (rx1 + 4, max(ry1 - 8, 12)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, ROI_BORDER_COLOR, 1, cv2.LINE_AA)

    for det in detections:
        color = ROI_HIT_COLOR if det["inside_roi"] else BOX_COLOR
        x1, y1, x2, y2 = int(det["x1"]), int(det["y1"]), int(det["x2"]), int(det["y2"])
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{det['class']} {det['confidence']:.0%}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
        cv2.putText(frame, label, (x1 + 3, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (10, 10, 10), 1, cv2.LINE_AA)
    return frame


def _process_one_frame(camera: CameraService, detector: YoloDetector) -> dict | None:
    """Blocking work (camera read + YOLO inference) meant to run in a thread executor."""
    frame = camera.read_frame()
    if frame is None:
        return None

    h, w = frame.shape[:2]
    raw_detections = detector.detect(frame, state.confidence_threshold)

    detections = []
    for det in raw_detections:
        cx, cy = box_center(det.x1, det.y1, det.x2, det.y2)
        inside = state.roi.contains_point(cx, cy, w, h)
        detections.append({
            "class": det.class_name,
            "confidence": round(det.confidence, 4),
            "x1": det.x1, "y1": det.y1, "x2": det.x2, "y2": det.y2,
            "inside_roi": inside,
        })

    annotated = _draw_overlay(frame, detections, state.roi)
    image_data_url = _encode_frame_to_data_url(annotated)

    return {"detections": detections, "image": image_data_url}


async def run_detection_loop():
    """
    Long-running background task, started once on app startup.
    Only does real work while at least one client is connected and
    `state.running` is True, so an idle server doesn't spin the CPU
    or hold the webcam open unnecessarily.
    """
    loop = asyncio.get_event_loop()
    camera = get_camera()
    detector = get_detector()

    frame_counter = 0
    last_result_detections: list[dict] = []

    while True:
        if not manager.active:
            await asyncio.sleep(0.2)
            continue

        state.running = True
        frame_counter += 1
        run_detection = (frame_counter % settings.FRAME_SKIP == 0)

        try:
            if run_detection:
                result = await loop.run_in_executor(None, _process_one_frame, camera, detector)
            else:
                # Still grab a frame for a smooth-looking stream, but reuse the
                # last detection boxes instead of re-running YOLO on it.
                frame = await loop.run_in_executor(None, camera.read_frame)
                if frame is None:
                    await asyncio.sleep(0.05)
                    continue
                annotated = _draw_overlay(frame, last_result_detections, state.roi)
                result = {
                    "detections": last_result_detections,
                    "image": _encode_frame_to_data_url(annotated),
                }
        except RuntimeError as exc:
            logger.error("Camera error: %s", exc)
            await manager.broadcast({"type": "error", "message": str(exc)})
            await asyncio.sleep(1.0)
            continue

        if result is None:
            await asyncio.sleep(0.05)
            continue

        if run_detection:
            last_result_detections = result["detections"]
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
            for det in result["detections"]:
                insert_detection(det["class"], det["confidence"], det["inside_roi"], timestamp)

            roi_hits = [d for d in result["detections"] if d["inside_roi"]]
            alerts = evaluate_alerts(roi_hits, state.watched_classes)
            if alerts:
                await manager.broadcast({
                    "type": "alert",
                    "alerts": [a.__dict__ for a in alerts],
                })

        await manager.broadcast({
            "type": "frame",
            "image": result["image"],
            "detections": result["detections"],
            "confidence_threshold": state.confidence_threshold,
            "roi": [state.roi.x1, state.roi.y1, state.roi.x2, state.roi.y2],
        })

        await asyncio.sleep(1 / settings.TARGET_FPS)
