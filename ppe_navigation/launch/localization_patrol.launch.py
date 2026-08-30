from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetRemap


def generate_launch_description() -> LaunchDescription:
    share = Path(get_package_share_directory("ppe_navigation"))
    nav2_share = Path(get_package_share_directory("nav2_bringup"))
    map_file = LaunchConfiguration("map")
    params = LaunchConfiguration("params_file")
    route = LaunchConfiguration("route_file")
    enable_motion = LaunchConfiguration("enable_motion")
    nav2_group = GroupAction([
        SetRemap(src="/cmd_vel", dst="/cmd_vel_nav"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(nav2_share / "launch" / "bringup_launch.py")),
            launch_arguments={
                "map": map_file,
                "params_file": params,
                "use_sim_time": "false",
                "autostart": "true",
                "use_composition": "False",
            }.items(),
        ),
    ])
    return LaunchDescription([
        DeclareLaunchArgument("map", description="Absolute path to the saved plant map YAML"),
        DeclareLaunchArgument("params_file", default_value=str(share / "config" / "nav2_params.yaml")),
        DeclareLaunchArgument("route_file", default_value=str(share / "config" / "waypoints.example.yaml")),
        DeclareLaunchArgument("enable_motion", default_value="false"),
        nav2_group,
        Node(
            package="nav2_collision_monitor", executable="collision_monitor",
            name="collision_monitor", output="screen",
            parameters=[str(share / "config" / "collision_monitor.yaml")],
        ),
        Node(
            package="nav2_lifecycle_manager", executable="lifecycle_manager",
            name="lifecycle_manager_collision_monitor", output="screen",
            parameters=[{"autostart": True, "node_names": ["collision_monitor"]}],
        ),
        Node(
            package="ppe_navigation", executable="safety_supervisor",
            name="ppe_safety_supervisor", output="screen",
            parameters=[{"scan_topic": "/scan", "stop_distance": 0.40}],
        ),
        Node(
            package="ppe_navigation", executable="patrol_node",
            name="ppe_patrol", output="screen",
            parameters=[{
                "route_file": route,
                "enable_motion": enable_motion,
                "loop_route": True,
                "ppe_pause_seconds": 8.0,
            }],
        ),
    ])
