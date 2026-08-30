from __future__ import annotations

from abc import ABC, abstractmethod
from itertools import cycle
from pathlib import Path
from typing import Any

from .models import Box, Detection


class Detector(ABC):
    @abstractmethod
    def detect(self, image: Any) -> list[Detection]:
        raise NotImplementedError


class MockDetector(Detector):
    """Deterministic sequence used for demos and hardware-free tests."""

    def __init__(self) -> None:
        self._sequence = cycle([
            [Detection("person", 0.94, Box(100, 60, 360, 460))],
            [Detection("person", 0.95, Box(102, 60, 362, 460))],
            [Detection("person", 0.96, Box(104, 60, 364, 460))],
            [
                Detection("person", 0.95, Box(106, 60, 366, 460)),
                Detection("helmet", 0.89, Box(175, 70, 285, 160)),
                Detection("safety_vest", 0.91, Box(150, 190, 320, 350)),
            ],
        ])

    def detect(self, image: Any) -> list[Detection]:
        return next(self._sequence)


class UltralyticsDetector(Detector):
    def __init__(self, weights_path: str, confidence_threshold: float = 0.5) -> None:
        if not weights_path or not Path(weights_path).exists():
            raise FileNotFoundError(f"YOLO weights not found: {weights_path}")
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("Install ultralytics to use YOLO detection") from exc
        self.model = YOLO(weights_path)
        self.confidence_threshold = confidence_threshold

    def detect(self, image: Any) -> list[Detection]:
        results = self.model.predict(image, conf=self.confidence_threshold, verbose=False)
        detections: list[Detection] = []
        for result in results:
            names = result.names
            for raw in result.boxes:
                class_id = int(raw.cls.item())
                confidence = float(raw.conf.item())
                xmin, ymin, xmax, ymax = map(float, raw.xyxy[0].tolist())
                label = str(names[class_id]).lower().replace(" ", "_")
                if label == "vest":
                    label = "safety_vest"
                detections.append(Detection(label, confidence, Box(xmin, ymin, xmax, ymax)))
        return detections
