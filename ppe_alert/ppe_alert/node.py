from __future__ import annotations

import rclpy
from rclpy.node import Node
from ppe_interfaces.msg import PPEEvent
from std_msgs.msg import String

from .voice import EspeakVoiceAlert, MockVoiceAlert


class PPEAlertNode(Node):
    def __init__(self) -> None:
        super().__init__("ppe_alert")
        self.declare_parameter("enable_voice", False)
        self.voice = EspeakVoiceAlert() if self.get_parameter("enable_voice").value else MockVoiceAlert()
        self.publisher = self.create_publisher(String, "/ppe/voice_alert", 10)
        self.create_subscription(PPEEvent, "/ppe/events", self.on_event, 10)

    def on_event(self, event: PPEEvent) -> None:
        queued = self.voice.submit(event.alert_message)
        status = String()
        status.data = f"{event.event_id}:{'queued' if queued else 'rejected'}"
        self.publisher.publish(status)

    def destroy_node(self) -> bool:
        self.voice.close()
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = PPEAlertNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
