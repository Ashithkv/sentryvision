import { useDetectionSocket } from "../services/websocketService";
import CameraView from "../components/CameraView";
import ConfidenceSlider from "../components/ConfidenceSlider";
import ObjectSelector from "../components/ObjectSelector";
import AlertPanel from "../components/AlertPanel";
import HistoryTable from "../components/HistoryTable";

export default function Dashboard() {
  const { status, frame, detections, alerts, cameraError, config, sendConfig } = useDetectionSocket();

  return (
    <div className="min-h-screen bg-void px-4 py-4 md:px-6 md:py-6">
      <header className="mb-5 flex items-center justify-between border-b border-hairline pb-4">
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight text-ink">SentryVision</h1>
          <p className="font-mono text-xs text-muted">real-time YOLOv8 object detection console</p>
        </div>
        <div className="flex items-center gap-2 rounded border border-hairline px-3 py-1.5">
          <span className={`h-2 w-2 rounded-full ${status === "open" ? "bg-signal animate-pulse" : "bg-alert"}`} />
          <span className="font-mono text-xs text-muted">
            backend {status === "open" ? "connected" : status}
          </span>
        </div>
      </header>

      <main className="grid grid-cols-1 gap-5 lg:grid-cols-[1.6fr_1fr]">
        <section className="space-y-5">
          <div className="rounded border border-hairline bg-panel p-4">
            <CameraView
              frame={frame}
              cameraError={cameraError}
              connectionStatus={status}
              roi={config.roi}
              onRoiChange={(roi) => sendConfig({ roi })}
              detectionCount={detections.length}
            />
          </div>
          <div className="rounded border border-hairline bg-panel p-4" style={{ height: "340px" }}>
            <HistoryTable refreshSignal={alerts.length} />
          </div>
        </section>

        <aside className="space-y-5">
          <div className="space-y-5 rounded border border-hairline bg-panel p-4">
            <ConfidenceSlider
              value={config.confidence_threshold}
              onChange={(v) => sendConfig({ confidence: v })}
            />
            <div className="border-t border-hairline pt-4">
              <ObjectSelector
                availableClasses={config.available_classes}
                watchedClasses={config.watched_classes}
                onChange={(classes) => sendConfig({ watched_classes: classes })}
              />
            </div>
          </div>

          <div className="rounded border border-hairline bg-panel p-4">
            <AlertPanel alerts={alerts} />
          </div>
        </aside>
      </main>
    </div>
  );
}
