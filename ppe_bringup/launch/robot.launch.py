from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    config = str(Path(get_package_share_directory("ppe_bringup")) / "config" / "robot.yaml")
    return LaunchDescription([
        Node(package="ppe_perception", executable="perception_node", parameters=[config]),
        Node(package="ppe_decision", executable="decision_node", parameters=[config]),
        Node(package="ppe_alert", executable="alert_node", parameters=[config]),
        Node(package="ppe_logger", executable="logger_node", parameters=[config]),
        Node(package="ppe_navigation", executable="navigation_guard", parameters=[config]),
    ])
