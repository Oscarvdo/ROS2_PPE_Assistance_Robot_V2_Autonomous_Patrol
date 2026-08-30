from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def save_evidence(image: object, root: str | Path, event_id: str) -> str:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required to save evidence images") from exc
    today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    directory = Path(root) / today
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{event_id}.jpg"
    if not cv2.imwrite(str(path), image):
        raise OSError(f"Could not write evidence image: {path}")
    return str(path)
