from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from enum import Enum

from ppe_perception.models import ComplianceState, PersonObservation


class EventState(str, Enum):
    CLEAR = "CLEAR"
    OBSERVING = "OBSERVING"
    VIOLATION_PENDING = "VIOLATION_PENDING"
    ALERTED = "ALERTED"
    COOLDOWN = "COOLDOWN"


ALERT_MESSAGES = {
    ComplianceState.MISSING_HELMET: "Attention. Safety helmet required.",
    ComplianceState.MISSING_VEST: "Attention. Safety vest required.",
    ComplianceState.MISSING_HELMET_AND_VEST:
        "Attention. Safety helmet and safety vest required.",
}


@dataclass(frozen=True)
class PPEEvent:
    event_id: str
    track_id: str
    violation_type: str
    state: str
    alert_message: str
    person_confidence: float
    helmet_confidence: float
    vest_confidence: float
    source: str


@dataclass
class TrackState:
    state: EventState = EventState.CLEAR
    violation: ComplianceState | None = None
    first_seen: float = 0.0
    frames: int = 0
    cooldown_until: float = 0.0


class ViolationStateMachine:
    def __init__(
        self,
        confirmation_frames: int = 3,
        confirmation_seconds: float = 1.0,
        cooldown_seconds: float = 15.0,
        clock=time.monotonic,
    ) -> None:
        if confirmation_frames < 1 or confirmation_seconds < 0 or cooldown_seconds < 0:
            raise ValueError("State-machine timing values must be non-negative")
        self.confirmation_frames = confirmation_frames
        self.confirmation_seconds = confirmation_seconds
        self.cooldown_seconds = cooldown_seconds
        self.clock = clock
        self._tracks: dict[str, TrackState] = {}

    def update(self, observation: PersonObservation) -> PPEEvent | None:
        now = self.clock()
        track = self._tracks.setdefault(observation.track_id, TrackState())
        compliance = observation.compliance_state

        if compliance in (ComplianceState.COMPLIANT, ComplianceState.UNKNOWN):
            track.state = EventState.CLEAR if compliance == ComplianceState.COMPLIANT else EventState.OBSERVING
            track.violation = None
            track.frames = 0
            track.first_seen = 0.0
            return None

        if track.state in (EventState.ALERTED, EventState.COOLDOWN):
            if now < track.cooldown_until:
                track.state = EventState.COOLDOWN
                return None
            track.state = EventState.CLEAR
            track.frames = 0

        if track.violation != compliance:
            track.violation = compliance
            track.first_seen = now
            track.frames = 1
            track.state = EventState.VIOLATION_PENDING
            return None

        track.frames += 1
        elapsed = now - track.first_seen
        confirmed = (
            track.frames >= self.confirmation_frames
            and elapsed >= self.confirmation_seconds
        )
        if not confirmed:
            track.state = EventState.VIOLATION_PENDING
            return None

        track.state = EventState.ALERTED
        track.cooldown_until = now + self.cooldown_seconds
        message = ALERT_MESSAGES[compliance]
        return PPEEvent(
            event_id=str(uuid.uuid4()),
            track_id=observation.track_id,
            violation_type=compliance.value,
            state=track.state.value,
            alert_message=message,
            person_confidence=observation.person_confidence,
            helmet_confidence=observation.helmet_confidence,
            vest_confidence=observation.vest_confidence,
            source=observation.source,
        )

    def state_for(self, track_id: str) -> EventState | None:
        track = self._tracks.get(track_id)
        return track.state if track else None
