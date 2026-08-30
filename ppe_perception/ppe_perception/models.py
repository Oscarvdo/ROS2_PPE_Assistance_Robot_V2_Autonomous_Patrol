from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ComplianceState(str, Enum):
    COMPLIANT = "COMPLIANT"
    MISSING_HELMET = "MISSING_HELMET"
    MISSING_VEST = "MISSING_VEST"
    MISSING_HELMET_AND_VEST = "MISSING_HELMET_AND_VEST"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Box:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    @property
    def width(self) -> float:
        return max(0.0, self.xmax - self.xmin)

    @property
    def height(self) -> float:
        return max(0.0, self.ymax - self.ymin)

    @property
    def center(self) -> tuple[float, float]:
        return ((self.xmin + self.xmax) / 2.0, (self.ymin + self.ymax) / 2.0)

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    box: Box


@dataclass
class PersonObservation:
    track_id: str
    person_box: Box
    person_confidence: float
    helmet_detected: bool | None
    helmet_confidence: float
    vest_detected: bool | None
    vest_confidence: float
    compliance_state: ComplianceState
    source: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


def classify_compliance(
    helmet_detected: bool | None, vest_detected: bool | None
) -> ComplianceState:
    if helmet_detected is None or vest_detected is None:
        return ComplianceState.UNKNOWN
    if helmet_detected and vest_detected:
        return ComplianceState.COMPLIANT
    if not helmet_detected and not vest_detected:
        return ComplianceState.MISSING_HELMET_AND_VEST
    if not helmet_detected:
        return ComplianceState.MISSING_HELMET
    return ComplianceState.MISSING_VEST
