from __future__ import annotations

from .association import AssociationConfig, associate_ppe
from .detectors import Detector
from .models import PersonObservation, classify_compliance
from .tracker import IoUTracker


class PerceptionPipeline:
    def __init__(
        self,
        detector: Detector,
        tracker: IoUTracker | None = None,
        association_config: AssociationConfig | None = None,
        person_only_mode: bool = False,
    ) -> None:
        self.detector = detector
        self.tracker = tracker or IoUTracker()
        self.config = association_config or AssociationConfig()
        self.person_only_mode = person_only_mode

    def process(self, image: object, source: str = "unknown") -> list[PersonObservation]:
        detections = self.detector.detect(image)
        people = [item for item in detections if item.label == "person"]
        helmets = [item for item in detections if item.label == "helmet"]
        vests = [item for item in detections if item.label == "safety_vest"]
        track_ids = self.tracker.update([person.box for person in people])
        observations: list[PersonObservation] = []
        for person, track_id in zip(people, track_ids):
            helmet, vest = associate_ppe(person.box, helmets, vests, self.config)
            helmet_present = None if self.person_only_mode else helmet is not None
            vest_present = None if self.person_only_mode else vest is not None
            observations.append(PersonObservation(
                track_id=track_id,
                person_box=person.box,
                person_confidence=person.confidence,
                helmet_detected=helmet_present,
                helmet_confidence=helmet.confidence if helmet else 0.0,
                vest_detected=vest_present,
                vest_confidence=vest.confidence if vest else 0.0,
                compliance_state=classify_compliance(helmet_present, vest_present),
                source=source,
            ))
        return observations
