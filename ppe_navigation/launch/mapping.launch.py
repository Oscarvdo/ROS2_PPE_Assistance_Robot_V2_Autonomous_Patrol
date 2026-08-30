from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    share = Path(get_package_share_directory("ppe_navigation"))
    slam_share = Path(get_package_share_directory("slam_toolbox"))
    slam_params = LaunchConfiguration("slam_params")
    return LaunchDescription([
        DeclareLaunchArgument("slam_params", default_value=str(share / "config" / "slam_toolbox.yaml")),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(slam_share / "launch" / "online_async_launch.py")),
            launch_arguments={"slam_params_file": slam_params, "use_sim_time": "false"}.items(),
        ),
        Node(package="ppe_navigation", executable="safety_supervisor", name="ppe_safety_supervisor",
             parameters=[{"scan_topic": "/scan", "stop_distance": 0.40}]),
        Node(
            package="nav2_collision_monitor", executable="collision_monitor",
            name="collision_monitor", output="screen",
            parameters=[str(share / "config" / "collision_monitor.yaml")],
        ),
        Node(
            package="nav2_lifecycle_manager", executable="lifecycle_manager",
            name="lifecycle_manager_collision_monitor_mapping", output="screen",
            parameters=[{"autostart": True, "node_names": ["collision_monitor"]}],
        ),
    ])
