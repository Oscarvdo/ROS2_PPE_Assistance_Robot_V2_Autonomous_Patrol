from __future__ import annotations

from dataclasses import dataclass

from .models import Box


def iou(a: Box, b: Box) -> float:
    intersection = Box(
        max(a.xmin, b.xmin), max(a.ymin, b.ymin),
        min(a.xmax, b.xmax), min(a.ymax, b.ymax),
    ).area
    union = a.area + b.area - intersection
    return intersection / union if union > 0 else 0.0


@dataclass
class Track:
    track_id: str
    box: Box
    missed_frames: int = 0


class IoUTracker:
    def __init__(self, threshold: float = 0.3, max_missed_frames: int = 10) -> None:
        self.threshold = threshold
        self.max_missed_frames = max_missed_frames
        self._tracks: dict[str, Track] = {}
        self._next_id = 1

    def update(self, boxes: list[Box]) -> list[str]:
        unmatched_tracks = set(self._tracks)
        assignments: list[str] = []
        for box in boxes:
            candidates = [
                (iou(box, self._tracks[track_id].box), track_id)
                for track_id in unmatched_tracks
            ]
            score, track_id = max(candidates, default=(0.0, ""))
            if score >= self.threshold:
                track = self._tracks[track_id]
                track.box = box
                track.missed_frames = 0
                unmatched_tracks.remove(track_id)
            else:
                track_id = f"person-{self._next_id:04d}"
                self._next_id += 1
                self._tracks[track_id] = Track(track_id, box)
            assignments.append(track_id)

        for track_id in unmatched_tracks:
            self._tracks[track_id].missed_frames += 1
        self._tracks = {
            track_id: track for track_id, track in self._tracks.items()
            if track.missed_frames <= self.max_missed_frames
        }
        return assignments
