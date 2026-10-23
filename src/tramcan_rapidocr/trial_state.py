"""In-memory selection and freshness rules for the factory trial."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Viewport:
    """Map a letterboxed preview back to original camera pixels."""
    x: float
    y: float
    width: float
    height: float
    frame_width: int
    frame_height: int

    @classmethod
    def fit(cls, canvas_width, canvas_height, frame_width, frame_height):
        scale = min(canvas_width/frame_width, canvas_height/frame_height)
        width, height = frame_width*scale, frame_height*scale
        return cls((canvas_width-width)/2, (canvas_height-height)/2,
                   width, height, frame_width, frame_height)

    def region(self, start, end):
        def point(p):
            return (round(min(1, max(0, (p[0]-self.x)/self.width))*self.frame_width),
                    round(min(1, max(0, (p[1]-self.y)/self.height))*self.frame_height))
        a, b = point(start), point(end)
        x1, x2 = sorted((a[0], b[0]))
        y1, y2 = sorted((a[1], b[1]))
        return (x1, y1, x2, y2) if x2-x1 >= 12 and y2-y1 >= 8 else None


@dataclass
class TrialSession:
    revision: int = 0
    roi: tuple[int, int, int, int] | None = None

    def change(self, roi=None):
        self.revision += 1
        self.roi = roi

    def accepts(self, revision, captured_at, now, *, max_age=2.5):
        return revision == self.revision and 0 <= now-captured_at <= max_age
