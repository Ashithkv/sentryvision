"""
Decides whether a frame's detections should raise an alert.

Rule is intentionally simple and stated once here so it's the single
source of truth: an alert fires when a detection whose class is in
the user's selected watch-list has its center point inside the ROI.
"""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Alert:
    object_class: str
    confidence: float
    timestamp: str
    message: str


def evaluate_alerts(detections_in_roi: list[dict], watched_classes: set[str]) -> list[Alert]:
    """
    `detections_in_roi` is a list of detection dicts that have already
    been confirmed to be inside the ROI (see detection_service). This
    function only decides which of *those* are on the watch-list.
    """
    alerts: list[Alert] = []
    for det in detections_in_roi:
        if det["class"] in watched_classes:
            ts = datetime.now(timezone.utc).isoformat()
            alerts.append(
                Alert(
                    object_class=det["class"],
                    confidence=det["confidence"],
                    timestamp=ts,
                    message=f"{det['class']} detected inside ROI "
                            f"({det['confidence']:.0%} confidence)",
                )
            )
    return alerts
