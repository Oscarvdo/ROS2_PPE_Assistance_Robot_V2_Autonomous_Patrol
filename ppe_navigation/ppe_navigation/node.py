from __future__ import annotations

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from ppe_interfaces.msg import PPEEvent


class PPENavigationGuardNode(Node):
    """Safety boundary for future Nav2 work; this MVP never commands motion."""

    def __init__(self) -> None:
        super().__init__("ppe_navigation_guard")
        self.declare_parameter("dry_run", True)
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.publisher = self.create_publisher(
            Twist, str(self.get_parameter("cmd_vel_topic").value), 10
        )
        self.create_subscription(PPEEvent, "/ppe/events", self.on_event, 10)
        if not self.get_parameter("dry_run").value:
            self.get_logger().warning(
                "dry_run=false, but autonomous motion is intentionally not implemented in MVP"
            )

    def on_event(self, event: PPEEvent) -> None:
        self.get_logger().info(
            f"Navigation request suppressed for event {event.event_id}; MVP is observation-only"
        )


def main() -> None:
    rclpy.init()
    node = PPENavigationGuardNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
