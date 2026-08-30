from ppe_perception.association import AssociationConfig, associate_ppe
from ppe_perception.models import Box, ComplianceState, Detection, classify_compliance
from ppe_perception.tracker import IoUTracker, iou


def test_ppe_association_uses_head_and_torso_regions():
    person = Box(0, 0, 100, 200)
    helmet = Detection("helmet", 0.9, Box(25, 5, 75, 45))
    vest = Detection("safety_vest", 0.8, Box(20, 70, 80, 150))
    result = associate_ppe(person, [helmet], [vest], AssociationConfig())
    assert result == (helmet, vest)


def test_outside_ppe_is_not_associated():
    person = Box(0, 0, 100, 200)
    outside = Detection("helmet", 0.9, Box(200, 5, 250, 45))
    helmet, _ = associate_ppe(person, [outside], [], AssociationConfig())
    assert helmet is None


def test_compliance_states():
    assert classify_compliance(True, True) == ComplianceState.COMPLIANT
    assert classify_compliance(False, True) == ComplianceState.MISSING_HELMET
    assert classify_compliance(True, False) == ComplianceState.MISSING_VEST
    assert classify_compliance(False, False) == ComplianceState.MISSING_HELMET_AND_VEST
    assert classify_compliance(None, True) == ComplianceState.UNKNOWN


def test_tracker_keeps_and_expires_identity():
    tracker = IoUTracker(threshold=0.2, max_missed_frames=1)
    first = tracker.update([Box(0, 0, 100, 100)])[0]
    second = tracker.update([Box(5, 5, 105, 105)])[0]
    assert first == second
    tracker.update([])
    tracker.update([])
    third = tracker.update([Box(5, 5, 105, 105)])[0]
    assert third != first
    assert iou(Box(0, 0, 10, 10), Box(0, 0, 10, 10)) == 1.0
