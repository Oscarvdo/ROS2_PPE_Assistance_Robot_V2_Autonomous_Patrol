from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    nav_share = Path(get_package_share_directory("ppe_navigation"))
    robot_config = str(Path(get_package_share_directory("ppe_bringup")) / "config" / "robot.yaml")
    map_file = LaunchConfiguration("map")
    route_file = LaunchConfiguration("route_file")
    enable_motion = LaunchConfiguration("enable_motion")
    return LaunchDescription([
        DeclareLaunchArgument("map", description="Absolute path to plant map YAML"),
        DeclareLaunchArgument("route_file", default_value=str(nav_share / "config" / "waypoints.example.yaml")),
        DeclareLaunchArgument("enable_motion", default_value="false"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(nav_share / "launch" / "localization_patrol.launch.py")),
            launch_arguments={
                "map": map_file,
                "route_file": route_file,
                "enable_motion": enable_motion,
            }.items(),
        ),
        Node(package="ppe_perception", executable="perception_node", name="ppe_perception", parameters=[robot_config]),
        Node(package="ppe_decision", executable="decision_node", name="ppe_decision", parameters=[robot_config]),
        Node(package="ppe_alert", executable="alert_node", name="ppe_alert", parameters=[robot_config]),
        Node(package="ppe_logger", executable="logger_node", name="ppe_logger", parameters=[robot_config]),
    ])
