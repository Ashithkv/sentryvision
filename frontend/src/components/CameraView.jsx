import { useRef, useState } from "react";

/**
 * Renders the annotated JPEG frame the backend already drew boxes on,
 * plus a draggable rectangle the user can redraw to move the ROI.
 * The backend does the real box/ROI drawing (baked into the JPEG) so
 * this component's own overlay is only for *editing* the ROI, not for
 * rendering detections — that keeps the two responsibilities honest:
 * the backend is the source of truth for what's inside the ROI.
 */
export default function CameraView({ frame, cameraError, connectionStatus, roi, onRoiChange, detectionCount }) {
  const containerRef = useRef(null);
  const [dragStart, setDragStart] = useState(null);
  const [dragRect, setDragRect] = useState(null);

  const getNormalizedPoint = (e) => {
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
    const y = Math.min(1, Math.max(0, (e.clientY - rect.top) / rect.height));
    return [x, y];
  };

  const handleMouseDown = (e) => {
    const point = getNormalizedPoint(e);
    setDragStart(point);
    setDragRect([point[0], point[1], point[0], point[1]]);
  };

  const handleMouseMove = (e) => {
    if (!dragStart) return;
    const [x, y] = getNormalizedPoint(e);
    setDragRect([dragStart[0], dragStart[1], x, y]);
  };

  const handleMouseUp = () => {
    if (dragRect) {
      const [x1, y1, x2, y2] = dragRect;
      if (Math.abs(x2 - x1) > 0.03 && Math.abs(y2 - y1) > 0.03) {
        onRoiChange([
          Math.min(x1, x2), Math.min(y1, y2),
          Math.max(x1, x2), Math.max(y1, y2),
        ]);
      }
    }
    setDragStart(null);
    setDragRect(null);
  };

  const displayRoi = dragRect || roi;
  const [rx1, ry1, rx2, ry2] = displayRoi;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-sm font-semibold tracking-wide text-ink">Live feed</h2>
        <div className="flex items-center gap-2 font-mono text-xs text-muted">
          <span className={`h-2 w-2 rounded-full ${connectionStatus === "open" ? "bg-signal" : "bg-alert"}`} />
          {connectionStatus === "open" ? "streaming" : connectionStatus}
          {connectionStatus === "open" && (
            <span className="text-muted">· {detectionCount} objects</span>
          )}
        </div>
      </div>

      <div
        ref={containerRef}
        className="relative aspect-[4/3] w-full select-none overflow-hidden rounded border border-hairline bg-panel"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {frame ? (
          <img src={frame} alt="Live camera feed with detections" className="h-full w-full object-cover" draggable={false} />
        ) : (
          <div className="flex h-full w-full items-center justify-center font-mono text-xs text-muted">
            waiting for camera stream…
          </div>
        )}

        {/* editable ROI handle — dashed while dragging, solid otherwise */}
        <div
          className={`pointer-events-none absolute border-2 ${dragRect ? "border-dashed" : "border-solid"} border-roi/90`}
          style={{
            left: `${rx1 * 100}%`,
            top: `${ry1 * 100}%`,
            width: `${(rx2 - rx1) * 100}%`,
            height: `${(ry2 - ry1) * 100}%`,
          }}
        />

        {cameraError && (
          <div className="absolute inset-0 flex items-center justify-center bg-void/90 p-6 text-center">
            <div>
              <p className="font-display text-sm font-semibold text-alert">Camera unavailable</p>
              <p className="mt-1 font-mono text-xs text-muted">{cameraError}</p>
            </div>
          </div>
        )}
      </div>
      <p className="font-mono text-[11px] text-muted">Click and drag on the feed to redraw the ROI rectangle.</p>
    </div>
  );
}
