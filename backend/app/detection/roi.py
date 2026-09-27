"""
Region-of-interest geometry.

Deliberately tiny: an ROI is just a rectangle stored as normalized
(0..1) fractions of the frame so it stays valid even if the camera
resolution changes. "Is this detection inside the ROI?" is answered
with a single point-in-rectangle test on the detection's center point
— no polygon math, no tracking, nothing fancy.
"""

from dataclasses import dataclass


@dataclass
class ROI:
    x1: float
    y1: float
    x2: float
    y2: float

    @classmethod
    def from_tuple(cls, box: tuple[float, float, float, float]) -> "ROI":
        x1, y1, x2, y2 = box
        return cls(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    def to_pixels(self, frame_width: int, frame_height: int) -> tuple[int, int, int, int]:
        """Convert the normalized rectangle to pixel coordinates for drawing."""
        return (
            int(self.x1 * frame_width),
            int(self.y1 * frame_height),
            int(self.x2 * frame_width),
            int(self.y2 * frame_height),
        )

    def contains_point(self, x: float, y: float, frame_width: int, frame_height: int) -> bool:
        """x, y are pixel coordinates of a detection's center point."""
        px1, py1, px2, py2 = self.to_pixels(frame_width, frame_height)
        return px1 <= x <= px2 and py1 <= y <= py2


def box_center(x1: float, y1: float, x2: float, y2: float) -> tuple[float, float]:
    """Center point of a bounding box, in the same units as the box."""
    return (x1 + x2) / 2, (y1 + y2) / 2
