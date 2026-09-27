# SentryVision

A small, fully working real-time object detection dashboard. Point a
webcam at the backend, watch YOLOv8 draw boxes around whatever it
sees, define a rectangular "region of interest" (ROI) on the video,
and get an alert the moment a chosen object class (person, car,
truck, ...) walks into that zone. Every detection is logged to
SQLite so you can review history later.

This is a portfolio project. It is deliberately scoped to **one
camera, one model, one ROI, one alert rule** — no user accounts, no
multi-camera fan-out, no training pipeline. The goal is to
demonstrate the full real-time pipeline (camera → inference → alert
→ live UI → persistence) cleanly enough that every piece is easy to
explain in an interview.

```
sentryvision/
  backend/
    app/
      main.py            FastAPI app, startup/shutdown hooks
      config.py           All tunable settings in one place
      database.py          SQLite access (no ORM)
      routes/
        detections.py       GET/DELETE /detections
        websocket.py         WS /ws/detection
      services/
        camera_service.py    Owns cv2.VideoCapture
        detection_service.py The main loop: camera -> YOLO -> ROI -> broadcast -> persist
        alert_service.py     Decides which ROI hits become alerts
      detection/
        yolo_detector.py     Thin wrapper around ultralytics YOLO
        roi.py               ROI rectangle + point-in-rect math
    models/                yolov8n.pt lives here (auto-downloaded)
    requirements.txt

  frontend/
    src/
      components/         CameraView, ConfidenceSlider, ObjectSelector,
                           AlertPanel, HistoryTable
      pages/Dashboard.jsx  Composes the whole dashboard
      services/
        websocketService.js  useDetectionSocket() hook
        api.js                REST calls for /detections
      App.jsx
  README.md   <- you are here
```

## How it works

### 1. Camera capture (OpenCV)

`CameraService` wraps `cv2.VideoCapture`. It opens the webcam once,
sets a modest resolution (640x480 by default), and hands back raw
BGR frames on request. Nothing else in the codebase talks to OpenCV's
capture API directly — if you ever swap the source for an IP camera
or a video file, this is the only file that changes.

### 2. YOLO detection (Ultralytics YOLOv8)

`YoloDetector` loads a **pretrained** `yolov8n.pt` (the "nano" YOLOv8
variant, trained on COCO's 80 everyday object classes: person, car,
truck, dog, backpack, etc). No training happens anywhere in this
project — `model.predict(frame, conf=threshold)` runs one forward
pass per frame and returns bounding boxes, class ids, and confidence
scores, which get converted into simple `Detection` objects.

YOLO ("You Only Look Once") is a single-pass detector: unlike older
two-stage detectors (e.g. R-CNN) that first propose regions and then
classify each one, YOLO treats detection as one regression problem
over the whole image, predicting all boxes and classes in a single
forward pass. That's what makes it fast enough for real-time video
on a single CPU-only laptop, which is why it fits this project.

### 3. ROI logic

The ROI is stored as four normalized floats (`x1, y1, x2, y2`, each
0..1 as a fraction of frame width/height) rather than pixel
coordinates, so it stays valid even if the camera resolution changes.
Checking whether a detection is "inside" the ROI is intentionally the
simplest possible test: take the detection box's **center point**
and check if it falls inside the ROI rectangle (`roi.py:contains_point`).
No polygon clipping, no IoU, no tracking across frames — a center-point
test is enough for a bounding-box-vs-rectangle containment check and
is trivial to reason about.

### 4. WebSocket streaming

`/ws/detection` is a single long-lived WebSocket. On connect, the
server sends an `init` message (current confidence threshold, ROI,
watched classes, and the full COCO class list so the frontend can
populate its selectors). After that, the server pushes one `frame`
message per processed frame:

```json
{
  "type": "frame",
  "image": "data:image/jpeg;base64,...",
  "detections": [
    { "class": "person", "confidence": 0.91, "inside_roi": true, "x1": 120.4, "y1": 60.1, "x2": 240.7, "y2": 300.9 }
  ],
  "confidence_threshold": 0.5,
  "roi": [0.25, 0.25, 0.75, 0.75]
}
```

and a separate `alert` message whenever a watched class enters the
ROI. The frontend can also *send* the server a `config` message at
any time (`{"type": "config", "confidence": 0.6, "roi": [...], "watched_classes": [...]}`)
to change the threshold, redraw the ROI, or change which classes
trigger alerts — no reconnect needed.

WebSockets were the right fit here over plain REST polling because
the server needs to **push** a new annotated frame to the browser
many times a second; polling would mean the browser constantly
asking "anything new?" and either wasting requests or adding lag.
A single persistent connection lets the server push the moment a
frame is ready.

### 5. FastAPI backend

FastAPI hosts both the REST routes (`/health`, `/detections`) and the
WebSocket route in one ASGI app. A single background `asyncio` task
(`run_detection_loop`) owns the camera and the model instance, and
loops: read a frame → (every Nth frame) run YOLO → check ROI → draw
boxes → JPEG-encode → broadcast to every connected client → persist
to SQLite. Using one shared loop instead of one loop per browser tab
keeps things simple: there's only one camera and one model to manage,
and every connected client just gets a copy of the same stream.

### 6. React dashboard (Vite + Tailwind)

- **CameraView** — shows the annotated JPEG stream and lets you
  click-and-drag directly on the video to redraw the ROI.
- **ConfidenceSlider** — live-adjusts the detection confidence cutoff.
- **ObjectSelector** — searchable checklist of COCO classes to watch
  for ROI alerts.
- **AlertPanel** — live feed of "object X entered the ROI" events.
- **HistoryTable** — polls `GET /detections` and lets you clear
  history via `DELETE /detections`.

All live data flows through one hook, `useDetectionSocket()`, which
owns the WebSocket connection, reconnects automatically if the
backend restarts, and exposes plain React state.

### 7. Detection history (SQLite)

Every processed detection — not just ROI hits — is written to a
single `detections` table (`id, object_class, confidence, inside_roi,
timestamp`) using plain `sqlite3` with parameterized queries. No ORM:
the project only ever needs insert / list / clear, so `database.py`
is ~50 lines and easy to read top to bottom.

### 8. Performance choices

- **Frame skipping** (`FRAME_SKIP`, default 2): YOLO only runs on
  every Nth captured frame; frames in between reuse the last known
  boxes so the video still looks smooth without paying the inference
  cost every frame.
- **Modest resolution** (640x480 default): keeps both the JPEG
  payload and the inference cost small enough for real-time use on a
  CPU.
- **yolov8n** (nano): the smallest, fastest YOLOv8 variant — the
  right tradeoff for a live CPU demo over the larger, more accurate
  variants.

None of this introduces distributed processing, queues, or GPU
requirements — it's all single-process, single-camera, and meant to
run on a laptop.

## API reference

| Method | Path              | Description                                  |
|--------|-------------------|-----------------------------------------------|
| GET    | `/health`         | Liveness check                                |
| GET    | `/detections`      | Recent detection history (`?limit=`, `?only_roi=`) |
| DELETE | `/detections`      | Clear detection history                       |
| WS     | `/ws/detection`    | Live annotated frame stream + alerts + config |

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The first time it starts, Ultralytics will download `yolov8n.pt`
automatically (~6MB) if it isn't already in `backend/models/`.

The backend opens webcam index `0` by default. Change it with the
`SENTRYVISION_CAMERA_INDEX` environment variable if you have more
than one camera. If no camera is available, the server stays up and
broadcasts a friendly `error` message over the WebSocket instead of
crashing — the frontend shows this as "Camera unavailable".

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (default `http://localhost:5173`). It
expects the backend at `http://localhost:8000` / `ws://localhost:8000`
by default; override with `VITE_API_BASE` / `VITE_WS_BASE` env vars
if you're running the backend elsewhere.

### Try it

1. Start the backend, then the frontend.
2. Allow a second for the model to load — the video feed will
   populate once a client connects and the camera opens successfully.
3. Drag on the video to move the ROI.
4. Check "person" (or any class) in "Watched objects".
5. Walk into the ROI — an alert should appear within a second, and a
   new row should show up in the history table.

## What was verified locally while building this

- Backend imports cleanly and `/health` returns `200`.
- The YOLO model loads (auto-downloading `yolov8n.pt`) and runs
  inference successfully on a sample frame.
- The ROI point-in-rectangle logic was checked against a known point.
- The WebSocket handshake, `init` message, and `config` update/ack
  round-trip were exercised end-to-end against a running server.
- With no camera attached, the pipeline degrades gracefully — it
  broadcasts a WebSocket `error` message instead of crashing the
  server, which the UI surfaces as "Camera unavailable".
- `GET /detections` and `DELETE /detections` were hit directly.
- The frontend builds with `vite build` with no errors and serves
  correctly under `vite dev`, with all component modules resolving.
