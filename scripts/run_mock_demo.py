#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for package in ("ppe_perception", "ppe_decision", "ppe_alert", "ppe_logger"):
    sys.path.insert(0, str(ROOT / package))

from ppe_alert.voice import MockVoiceAlert
from ppe_decision.state_machine import ViolationStateMachine
from ppe_logger.repository import EventRepository
from ppe_perception.detectors import MockDetector
from ppe_perception.pipeline import PerceptionPipeline


class DemoClock:
    def __init__(self): self.value = 0.0
    def __call__(self): return self.value
    def advance(self): self.value += 0.5


def main() -> None:
    clock = DemoClock()
    pipeline = PerceptionPipeline(MockDetector())
    decision = ViolationStateMachine(3, 1.0, 5.0, clock)
    voice = MockVoiceAlert()
    database = ROOT / "data" / "mock_events.db"
    if database.exists():
        database.unlink()
    repository = EventRepository(database)

    for frame_number in range(1, 9):
        observations = pipeline.process(None, "mock_demo")
        for observation in observations:
            print(f"frame={frame_number} track={observation.track_id} state={observation.compliance_state.value}")
            event = decision.update(observation)
            if event:
                voice.submit(event.alert_message)
                repository.insert(event, alert_status="mocked")
                print(f"EVENT {event.violation_type}: {event.alert_message}")
        clock.advance()
    print(f"Stored events: {repository.count()} in {database}")
    print(f"Voice messages: {voice.messages}")


if __name__ == "__main__":
    main()
