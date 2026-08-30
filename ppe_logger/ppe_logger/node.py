from __future__ import annotations

import json

import rclpy
from rclpy.node import Node
from ppe_interfaces.msg import PPEEvent
from ppe_decision.state_machine import PPEEvent as CoreEvent

from .repository import EventRepository


class PPELoggerNode(Node):
    def __init__(self) -> None:
        super().__init__("ppe_logger")
        self.declare_parameter("database_path", "data/ppe_events.db")
        self.repository = EventRepository(self.get_parameter("database_path").value)
        self.create_subscription(PPEEvent, "/ppe/events", self.on_event, 10)

    def on_event(self, message: PPEEvent) -> None:
        event = CoreEvent(
            message.event_id, message.track_id, message.violation_type,
            message.state, message.alert_message, message.person_confidence,
            message.helmet_confidence, message.vest_confidence, message.source,
        )
        metadata = json.loads(message.metadata_json or "{}")
        self.repository.insert(event, alert_status="published", metadata=metadata)


def main() -> None:
    rclpy.init()
    node = PPELoggerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
