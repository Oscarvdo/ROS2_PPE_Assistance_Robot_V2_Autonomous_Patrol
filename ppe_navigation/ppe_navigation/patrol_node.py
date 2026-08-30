from __future__ import annotations

import math
import time
from pathlib import Path

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from ppe_interfaces.msg import PPEEvent
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import Bool, String

from .route import Waypoint, load_route


class PPEPatrolNode(Node):
    def __init__(self) -> None:
        super().__init__("ppe_patrol")
        self.declare_parameter("route_file", "")
        self.declare_parameter("enable_motion", False)
        self.declare_parameter("loop_route", True)
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("ppe_pause_seconds", 8.0)
        self.declare_parameter("safety_stop_topic", "/ppe/safety_stop")
        route_file = str(self.get_parameter("route_file").value)
        if not route_file:
            raise ValueError("route_file parameter is required")
        self.route = load_route(Path(route_file))
        self.index = 0
        self.goal_handle = None
        self.goal_active = False
        self.safety_stop = True
        self.paused_until = 0.0
        self.dwell_until = 0.0
        self.client = ActionClient(self, NavigateToPose, "navigate_to_pose")
        self.status = self.create_publisher(String, "/ppe/patrol_status", 10)
        self.create_subscription(
            Bool, str(self.get_parameter("safety_stop_topic").value), self.on_safety, 10
        )
        self.create_subscription(PPEEvent, "/ppe/events", self.on_ppe_event, 10)
        self.create_timer(0.5, self.tick)
        if not self.get_parameter("enable_motion").value:
            self.get_logger().warning("Patrol loaded but enable_motion=false; no goals will be sent")

    def publish_status(self, value: str) -> None:
        message = String()
        message.data = value
        self.status.publish(message)

    def on_safety(self, message: Bool) -> None:
        previous = self.safety_stop
        self.safety_stop = bool(message.data)
        if self.safety_stop and not previous:
            self.cancel_active_goal("safety_stop")

    def on_ppe_event(self, event: PPEEvent) -> None:
        self.paused_until = time.monotonic() + float(self.get_parameter("ppe_pause_seconds").value)
        self.cancel_active_goal(f"ppe_event:{event.event_id}")

    def cancel_active_goal(self, reason: str) -> None:
        if self.goal_handle is not None and self.goal_active:
            self.goal_handle.cancel_goal_async()
        self.goal_active = False
        self.publish_status(f"paused:{reason}")

    def tick(self) -> None:
        if not self.get_parameter("enable_motion").value:
            return
        now = time.monotonic()
        if self.safety_stop or now < self.paused_until or now < self.dwell_until or self.goal_active:
            return
        if not self.client.wait_for_server(timeout_sec=0.1):
            self.publish_status("waiting_for_nav2")
            return
        self.send_waypoint(self.route[self.index])

    def send_waypoint(self, waypoint: Waypoint) -> None:
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = str(self.get_parameter("map_frame").value)
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = waypoint.x
        goal.pose.pose.position.y = waypoint.y
        goal.pose.pose.orientation.z = math.sin(waypoint.yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(waypoint.yaw / 2.0)
        self.goal_active = True
        self.publish_status(f"goal_sent:{waypoint.name}")
        future = self.client.send_goal_async(goal)
        future.add_done_callback(self.on_goal_response)

    def on_goal_response(self, future) -> None:
        self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.goal_active = False
            self.publish_status("goal_rejected")
            return
        result = self.goal_handle.get_result_async()
        result.add_done_callback(self.on_result)

    def on_result(self, future) -> None:
        wrapped = future.result()
        self.goal_active = False
        waypoint = self.route[self.index]
        if wrapped.status == GoalStatus.STATUS_SUCCEEDED:
            self.publish_status(f"arrived:{waypoint.name}")
            self.dwell_until = time.monotonic() + waypoint.dwell_seconds
            self.index += 1
            if self.index >= len(self.route):
                if self.get_parameter("loop_route").value:
                    self.index = 0
                else:
                    self.set_parameters([Parameter("enable_motion", Parameter.Type.BOOL, False)])
                    self.publish_status("route_complete")
        elif wrapped.status == GoalStatus.STATUS_CANCELED:
            self.publish_status(f"goal_canceled:{waypoint.name}")
        else:
            self.publish_status(f"goal_failed:{waypoint.name}:status={wrapped.status}")


def main() -> None:
    rclpy.init()
    node = PPEPatrolNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
