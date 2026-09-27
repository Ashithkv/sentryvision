import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routes import detections, websocket
from app.services.detection_service import run_detection_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("sentryvision.main")

app = FastAPI(title="SentryVision", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detections.router)
app.include_router(websocket.router)

_background_task: asyncio.Task | None = None


@app.on_event("startup")
async def on_startup():
    init_db()
    global _background_task
    _background_task = asyncio.create_task(run_detection_loop())
    logger.info("SentryVision backend started")


@app.on_event("shutdown")
async def on_shutdown():
    if _background_task:
        _background_task.cancel()


@app.get("/health")
def health():
    return {"status": "ok", "service": "sentryvision"}
