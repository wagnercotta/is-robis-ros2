from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
<<<<<<< Updated upstream
    publish_odom_tf = LaunchConfiguration("publish_odom_tf")
    publish_odom_tf_bool = ParameterValue(publish_odom_tf, value_type=bool)
=======
    namespace = LaunchConfiguration("namespace")
    frame_prefix = PythonExpression(["'", namespace, "'.strip('/')"])
    odom_frame = PathJoinSubstitution([frame_prefix, "odom"])
    base_footprint_frame = PathJoinSubstitution([frame_prefix, "base_footprint"])
    base_link_frame = PathJoinSubstitution([frame_prefix, "base_link"])

    namespace_argument = DeclareLaunchArgument(
        "namespace",
        default_value="",
        description="ROS namespace used by the ODrive nodes and TF frames.",
    )
>>>>>>> Stashed changes

    return LaunchDescription(
        [
            namespace_argument,
            Node(
                package="odrive_ros2_pkg",
                executable="odrive_node",
                name="odrive_node",
                namespace=namespace,
                output="screen",
                emulate_tty=True,
                parameters=[
                    {
                        "simulation_mode": False,
<<<<<<< Updated upstream
                        "wheel_track": 0.278,
                        "tyre_circumference": 0.5,
                        "publish_odom_tf": publish_odom_tf_bool,
=======
                        "wheel_track": 0.35,
                        "tyre_circumference": 0.537,
                        "odom_frame": odom_frame,
                        "base_frame": base_link_frame,
>>>>>>> Stashed changes
                    }
                ],
            ),
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="base_link_broadcaster",
<<<<<<< Updated upstream
                arguments=[
                    "0",
                    "0",
                    "0",
=======
                namespace=namespace,
                arguments=[
                    "0",
                    "0",
                    "0.06",
>>>>>>> Stashed changes
                    "0",
                    "0",
                    "0",
                    "1",
<<<<<<< Updated upstream
                    "base_link",
                    "base_footprint",
=======
                    base_footprint_frame,
                    base_link_frame,
>>>>>>> Stashed changes
                ],
            ),
        ]
    )
