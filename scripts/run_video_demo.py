#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for package in ("ppe_perception", "ppe_decision", "ppe_alert", "ppe_logger"):
    sys.path.insert(0, str(ROOT / package))

from ppe_alert.voice import EspeakVoiceAlert, MockVoiceAlert
from ppe_decision.state_machine import ViolationStateMachine
from ppe_logger.evidence import save_evidence
from ppe_logger.repository import EventRepository
from ppe_perception.detectors import MockDetector, UltralyticsDetector
from ppe_perception.pipeline import PerceptionPipeline


def parse_args():
    parser = argparse.ArgumentParser(description="Hardware-independent PPE video demo")
    parser.add_argument("--source", default="0", help="Webcam index, video, or image path")
    parser.add_argument("--mode", choices=("mock", "yolo"), default="mock")
    parser.add_argument("--weights", default="")
    parser.add_argument("--database", default="data/video_events.db")
    parser.add_argument("--evidence", default="evidence")
    parser.add_argument("--voice", action="store_true")
    parser.add_argument("--display", action="store_true")
    return parser.parse_args()


def annotate(cv2, image, observations):
    for item in observations:
        box = item.person_box
        color = (0, 180, 0) if item.compliance_state.value == "COMPLIANT" else (0, 0, 230)
        cv2.rectangle(image, (int(box.xmin), int(box.ymin)), (int(box.xmax), int(box.ymax)), color, 2)
        cv2.putText(image, f"{item.track_id} {item.compliance_state.value}",
                    (int(box.xmin), max(20, int(box.ymin) - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    return image


def main() -> None:
    args = parse_args()
    try:
        import cv2
    except ImportError as exc:
        raise SystemExit("Install opencv-python before using video mode") from exc
    detector = MockDetector() if args.mode == "mock" else UltralyticsDetector(args.weights)
    pipeline = PerceptionPipeline(detector)
    decision = ViolationStateMachine(3, 1.0, 15.0)
    voice = EspeakVoiceAlert() if args.voice else MockVoiceAlert()
    repository = EventRepository(ROOT / args.database)
    raw_source = int(args.source) if args.source.isdigit() else args.source
    capture = cv2.VideoCapture(raw_source)
    if not capture.isOpened():
        raise SystemExit(f"Could not open image source: {args.source}")
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            observations = pipeline.process(frame, str(args.source))
            for item in observations:
                event = decision.update(item)
                if event:
                    image_path = save_evidence(frame, ROOT / args.evidence, event.event_id)
                    queued = voice.submit(event.alert_message)
                    repository.insert(event, image_path, "queued" if queued else "rejected")
                    print(f"EVENT {event.event_id} {event.violation_type}")
            annotated = annotate(cv2, frame, observations)
            if args.display:
                cv2.imshow("PPE Assistance Robot", annotated)
                if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                    break
    finally:
        capture.release()
        voice.close()
        if args.display:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
