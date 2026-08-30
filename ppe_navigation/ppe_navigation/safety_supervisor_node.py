from __future__ import annotations

import json
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String

from .safety import SafetyDecision, evaluate_scan


class SafetySupervisorNode(Node):
    def __init__(self) -> None:
        super().__init__("ppe_safety_supervisor")
        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("safety_stop_topic", "/ppe/safety_stop")
        self.declare_parameter("stop_distance", 0.40)
        self.declare_parameter("lidar_timeout_seconds", 1.0)
        self.declare_parameter("startup_grace_seconds", 3.0)
        self._started = time.monotonic()
        self._last_scan_time: float | None = None
        self._decision = SafetyDecision(True, "waiting_for_lidar", None)
        self._external_estop = False
        stop_topic = str(self.get_parameter("safety_stop_topic").value)
        self.stop_publisher = self.create_publisher(Bool, stop_topic, 10)
        self.status_publisher = self.create_publisher(String, "/ppe/navigation_status", 10)
        self.create_subscription(
            LaserScan, str(self.get_parameter("scan_topic").value), self.on_scan, 10
        )
        self.create_subscription(Bool, "/ppe/emergency_stop", self.on_estop, 10)
        self.create_timer(0.1, self.publish_state)

    def on_scan(self, message: LaserScan) -> None:
        self._last_scan_time = time.monotonic()
        self._decision = evaluate_scan(
            list(message.ranges), message.range_min, message.range_max,
            float(self.get_parameter("stop_distance").value),
        )

    def on_estop(self, message: Bool) -> None:
        self._external_estop = bool(message.data)

    def publish_state(self) -> None:
        now = time.monotonic()
        timeout = float(self.get_parameter("lidar_timeout_seconds").value)
        grace = float(self.get_parameter("startup_grace_seconds").value)
        decision = self._decision
        if self._external_estop:
            decision = SafetyDecision(True, "external_emergency_stop", decision.nearest_obstacle)
        elif self._last_scan_time is None and now - self._started > grace:
            decision = SafetyDecision(True, "lidar_not_received", None)
        elif self._last_scan_time is not None and now - self._last_scan_time > timeout:
            decision = SafetyDecision(True, "lidar_timeout", decision.nearest_obstacle)
        stop = Bool()
        stop.data = decision.stop
        self.stop_publisher.publish(stop)
        status = String()
        status.data = json.dumps({
            "stop": decision.stop,
            "reason": decision.reason,
            "nearest_obstacle_m": decision.nearest_obstacle,
        })
        self.status_publisher.publish(status)


def main() -> None:
    rclpy.init()
    node = SafetySupervisorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
