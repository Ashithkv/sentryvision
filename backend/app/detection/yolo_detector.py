"""
Thin wrapper around a pretrained Ultralytics YOLOv8 model.

This module owns exactly one job: given a BGR frame (as produced by
OpenCV), return a list of plain-dict detections. It knows nothing
about ROI, WebSockets, or the database — keeping it single-purpose
makes it easy to unit test and easy to explain in an interview.
"""

import logging
from dataclasses import dataclass

from ultralytics import YOLO

from app.config import settings

logger = logging.getLogger("sentryvision.yolo")


@dataclass
class Detection:
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class YoloDetector:
    def __init__(self, model_path: str = settings.MODEL_PATH):
        logger.info("Loading YOLO model from %s", model_path)
        # Ultralytics transparently downloads the weights on first use
        # if `model_path` is a known model name (e.g. "yolov8n.pt") and
        # the file isn't present yet.
        self.model = YOLO(model_path)
        self.class_names = self.model.names  # {0: "person", 1: "bicycle", ...}

    def detect(self, frame, confidence_threshold: float) -> list[Detection]:
        """
        Run one forward pass on a single frame.

        `frame` is a numpy array (H, W, 3) in BGR order, exactly what
        cv2.VideoCapture.read() returns. Returns a list of Detection
        objects with pixel-space box coordinates.
        """
        results = self.model.predict(
            source=frame,
            conf=confidence_threshold,
            verbose=False,
        )

        detections: list[Detection] = []
        if not results:
            return detections

        boxes = results[0].boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            detections.append(
                Detection(
                    class_name=self.class_names.get(cls_id, str(cls_id)),
                    confidence=conf,
                    x1=x1, y1=y1, x2=x2, y2=y2,
                )
            )
        return detections

    def available_classes(self) -> list[str]:
        return list(self.class_names.values())
