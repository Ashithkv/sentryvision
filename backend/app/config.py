"""
Central configuration for SentryVision.

Everything here is a plain module-level constant so the rest of the
codebase can just `from app.config import settings` and read values
off a single object. Nothing exotic — this is a portfolio project,
not a 12-factor microservice.
"""

import os


class Settings:
    # --- Camera -------------------------------------------------------
    CAMERA_INDEX: int = int(os.getenv("SENTRYVISION_CAMERA_INDEX", "0"))
    FRAME_WIDTH: int = int(os.getenv("SENTRYVISION_FRAME_WIDTH", "640"))
    FRAME_HEIGHT: int = int(os.getenv("SENTRYVISION_FRAME_HEIGHT", "480"))
    TARGET_FPS: int = int(os.getenv("SENTRYVISION_TARGET_FPS", "15"))

    # Only run YOLO on every Nth captured frame. Detection is the
    # expensive step, so skipping frames is the simplest way to keep
    # the stream smooth on a CPU-only laptop.
    FRAME_SKIP: int = int(os.getenv("SENTRYVISION_FRAME_SKIP", "2"))

    # --- YOLO -----------------------------------------------------------
    # A pretrained COCO model. "yolov8n.pt" (nano) is the smallest/fastest
    # variant and downloads automatically the first time it's used if it
    # isn't already sitting in backend/models/.
    MODEL_PATH: str = os.getenv(
        "SENTRYVISION_MODEL_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "yolov8n.pt"),
    )
    DEFAULT_CONFIDENCE_THRESHOLD: float = float(
        os.getenv("SENTRYVISION_DEFAULT_CONFIDENCE", "0.5")
    )

    # --- ROI --------------------------------------------------------
    # Normalized (0..1) default ROI rectangle, expressed as
    # (x1, y1, x2, y2) fractions of frame width/height. The frontend
    # can override this at runtime via the WebSocket control channel.
    DEFAULT_ROI = (0.25, 0.25, 0.75, 0.75)

    # --- Alerts -------------------------------------------------------
    DEFAULT_ALERT_CLASSES = ["person"]

    # --- Database -------------------------------------------------------
    DATABASE_PATH: str = os.getenv(
        "SENTRYVISION_DB_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "sentryvision.db"),
    )

    # --- CORS (so the Vite dev server on :5173 can talk to :8000) -----
    ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


settings = Settings()
