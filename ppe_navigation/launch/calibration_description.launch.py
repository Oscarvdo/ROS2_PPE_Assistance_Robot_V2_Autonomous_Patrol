from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    xacro_file = Path(get_package_share_directory("ppe_navigation")) / "urdf" / "yahboom_ppe_calibration.urdf.xacro"
    description = ParameterValue(Command([
        "xacro ", str(xacro_file),
        " base_length:=", LaunchConfiguration("base_length"),
        " base_width:=", LaunchConfiguration("base_width"),
        " laser_x:=", LaunchConfiguration("laser_x"),
        " laser_z:=", LaunchConfiguration("laser_z"),
    ]), value_type=str)
    return LaunchDescription([
        DeclareLaunchArgument("base_length", default_value="0.36"),
        DeclareLaunchArgument("base_width", default_value="0.30"),
        DeclareLaunchArgument("laser_x", default_value="0.0"),
        DeclareLaunchArgument("laser_z", default_value="0.22"),
        Node(package="robot_state_publisher", executable="robot_state_publisher",
             parameters=[{"robot_description": description}]),
    ])
