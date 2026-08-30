from ppe_decision.state_machine import EventState, ViolationStateMachine
from ppe_perception.models import Box, ComplianceState, PersonObservation


class Clock:
    def __init__(self): self.now = 0.0
    def __call__(self): return self.now
    def advance(self, seconds): self.now += seconds


def observation(state, track_id="person-0001"):
    return PersonObservation(track_id, Box(0, 0, 100, 200), 0.95, False, 0.0,
                             False, 0.0, state, "test")


def test_single_frame_does_not_alert_and_persistent_violation_does():
    clock = Clock()
    machine = ViolationStateMachine(3, 1.0, 5.0, clock)
    assert machine.update(observation(ComplianceState.MISSING_HELMET)) is None
    clock.advance(0.5)
    assert machine.update(observation(ComplianceState.MISSING_HELMET)) is None
    clock.advance(0.5)
    event = machine.update(observation(ComplianceState.MISSING_HELMET))
    assert event is not None
    assert event.violation_type == "MISSING_HELMET"


def test_cooldown_and_compliance_restoration():
    clock = Clock()
    machine = ViolationStateMachine(2, 0.0, 10.0, clock)
    machine.update(observation(ComplianceState.MISSING_VEST))
    event = machine.update(observation(ComplianceState.MISSING_VEST))
    assert event is not None
    assert machine.update(observation(ComplianceState.MISSING_VEST)) is None
    assert machine.state_for("person-0001") == EventState.COOLDOWN
    assert machine.update(observation(ComplianceState.COMPLIANT)) is None
    assert machine.state_for("person-0001") == EventState.CLEAR


def test_unknown_never_alerts():
    machine = ViolationStateMachine(1, 0.0, 0.0)
    for _ in range(10):
        assert machine.update(observation(ComplianceState.UNKNOWN)) is None
    assert machine.state_for("person-0001") == EventState.OBSERVING
