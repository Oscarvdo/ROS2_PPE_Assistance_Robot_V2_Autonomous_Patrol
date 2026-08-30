from __future__ import annotations

import json

import rclpy
from rclpy.node import Node
from ppe_interfaces.msg import PPEEvent, PPEObservation

from ppe_perception.models import Box, ComplianceState, PersonObservation
from .state_machine import ViolationStateMachine


class PPEDecisionNode(Node):
    def __init__(self) -> None:
        super().__init__("ppe_decision")
        self.declare_parameter("violation_confirmation_frames", 3)
        self.declare_parameter("violation_confirmation_seconds", 1.0)
        self.declare_parameter("alert_cooldown_seconds", 15.0)
        self.machine = ViolationStateMachine(
            int(self.get_parameter("violation_confirmation_frames").value),
            float(self.get_parameter("violation_confirmation_seconds").value),
            float(self.get_parameter("alert_cooldown_seconds").value),
        )
        self.publisher = self.create_publisher(PPEEvent, "/ppe/events", 10)
        self.create_subscription(PPEObservation, "/ppe/observations", self.on_observation, 10)

    def on_observation(self, message: PPEObservation) -> None:
        observation = PersonObservation(
            message.track_id,
            Box(message.person_xmin, message.person_ymin, message.person_xmax, message.person_ymax),
            message.person_confidence,
            message.helmet_detected if message.helmet_status_known else None,
            message.helmet_confidence,
            message.vest_detected if message.vest_status_known else None,
            message.vest_confidence,
            ComplianceState(message.compliance_state),
            message.source,
        )
        event = self.machine.update(observation)
        if not event:
            return
        output = PPEEvent()
        output.header = message.header
        output.event_id = event.event_id
        output.track_id = event.track_id
        output.violation_type = event.violation_type
        output.state = event.state
        output.alert_message = event.alert_message
        output.person_confidence = event.person_confidence
        output.helmet_confidence = event.helmet_confidence
        output.vest_confidence = event.vest_confidence
        output.source = event.source
        output.metadata_json = json.dumps({"prototype": True})
        self.publisher.publish(output)


def main() -> None:
    rclpy.init()
    node = PPEDecisionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
