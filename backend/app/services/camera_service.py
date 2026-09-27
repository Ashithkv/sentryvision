"""
Wraps cv2.VideoCapture so the rest of the app never touches OpenCV's
capture API directly. Nothing here is YOLO- or WebSocket-aware — it
just knows how to open a webcam and hand back frames.
"""

import logging

import cv2

from app.config import settings

logger = logging.getLogger("sentryvision.camera")


class CameraService:
    def __init__(self, index: int = settings.CAMERA_INDEX):
        self.index = index
        self.capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        if self.capture is not None and self.capture.isOpened():
            return
        logger.info("Opening camera index %s", self.index)
        self.capture = cv2.VideoCapture(self.index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
        if not self.capture.isOpened():
            raise RuntimeError(
                f"Could not open webcam at index {self.index}. "
                "Check that a camera is connected and not in use by another app."
            )

    def read_frame(self):
        """Returns a BGR numpy frame, or None if the read failed."""
        if self.capture is None or not self.capture.isOpened():
            self.open()
        ok, frame = self.capture.read()
        if not ok:
            logger.warning("Failed to read frame from camera")
            return None
        return frame

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None
            logger.info("Camera released")
