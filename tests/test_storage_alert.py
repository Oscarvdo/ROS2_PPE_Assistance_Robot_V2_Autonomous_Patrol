from ppe_alert.voice import MockVoiceAlert
from ppe_decision.state_machine import PPEEvent
from ppe_logger.repository import EventRepository


def sample_event():
    return PPEEvent("event-1", "person-1", "MISSING_VEST", "ALERTED",
                    "Attention. Safety vest required.", 0.95, 0.8, 0.0, "test")


def test_mock_voice_alert():
    voice = MockVoiceAlert()
    assert voice.submit("hello")
    assert voice.messages == ["hello"]


def test_sqlite_insert(tmp_path):
    repository = EventRepository(tmp_path / "events.db")
    repository.insert(sample_event(), metadata={"test": True})
    assert repository.count() == 1
    row = repository.list_events()[0]
    assert row["violation_type"] == "MISSING_VEST"
    assert row["metadata_json"] == '{"test": true}'
