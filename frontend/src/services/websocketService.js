import { useCallback, useEffect, useRef, useState } from "react";

const WS_BASE = import.meta.env.VITE_WS_BASE || "ws://localhost:8000";
const MAX_ALERTS = 30;

/**
 * Owns the single WebSocket connection to /ws/detection and exposes
 * the live stream as plain React state. Handles reconnect-on-drop so
 * a backend restart doesn't require a page refresh.
 */
export function useDetectionSocket() {
  const [status, setStatus] = useState("connecting"); // connecting | open | closed
  const [frame, setFrame] = useState(null);
  const [detections, setDetections] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [cameraError, setCameraError] = useState(null);
  const [config, setConfig] = useState({
    confidence_threshold: 0.5,
    roi: [0.25, 0.25, 0.75, 0.75],
    watched_classes: [],
    available_classes: [],
  });

  const socketRef = useRef(null);
  const reconnectTimer = useRef(null);

  const connect = useCallback(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/detection`);
    socketRef.current = ws;
    setStatus("connecting");

    ws.onopen = () => setStatus("open");

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      switch (msg.type) {
        case "init":
          setConfig({
            confidence_threshold: msg.confidence_threshold,
            roi: msg.roi,
            watched_classes: msg.watched_classes,
            available_classes: msg.available_classes,
          });
          break;
        case "frame":
          setFrame(msg.image);
          setDetections(msg.detections || []);
          setCameraError(null);
          break;
        case "alert":
          setAlerts((prev) => [...msg.alerts, ...prev].slice(0, MAX_ALERTS));
          break;
        case "error":
          setCameraError(msg.message);
          break;
        default:
          break;
      }
    };

    ws.onclose = () => {
      setStatus("closed");
      reconnectTimer.current = setTimeout(connect, 2000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      socketRef.current?.close();
    };
  }, [connect]);

  const sendConfig = useCallback((partial) => {
    setConfig((prev) => {
      const next = { ...prev, ...partial };
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ type: "config", ...partial }));
      }
      return next;
    });
  }, []);

  return { status, frame, detections, alerts, cameraError, config, sendConfig };
}
