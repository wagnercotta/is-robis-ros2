from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import Node


def generate_launch_description():
    namespace = LaunchConfiguration("namespace")
    tf_remappings = [("/tf", "tf"), ("/tf_static", "tf_static")]
    frame_prefix = PythonExpression(["'", namespace, "'.strip('/')"])
    odom_frame = PathJoinSubstitution([frame_prefix, "odom"])
    base_footprint_frame = PathJoinSubstitution([frame_prefix, "base_footprint"])
    base_link_frame = PathJoinSubstitution([frame_prefix, "base_link"])

    namespace_argument = DeclareLaunchArgument(
        "namespace",
        default_value="",
        description="ROS namespace used by the ODrive nodes and TF frames.",
    )

    return LaunchDescription(
        [
            namespace_argument,
            Node(
                package="odrive_ros2_pkg",
                executable="odrive_node",
                name="odrive_node",
                namespace=namespace,
                remappings=tf_remappings,
                output="screen",
                emulate_tty=True,
                parameters=[
                    {
                        "simulation_mode": False,
                        "wheel_track": 0.35,
                        "tyre_circumference": 0.537,
                        "odom_frame": odom_frame,
                        "base_frame": base_link_frame,
                    }
                ],
            ),
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="base_link_broadcaster",
                namespace=namespace,
                remappings=tf_remappings,
                arguments=[
                    "0",
                    "0",
                    "0.06",
                    "0",
                    "0",
                    "0",
                    "1",
                    base_footprint_frame,
                    base_link_frame,
                ],
            ),
        ]
    )
