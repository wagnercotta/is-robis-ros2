import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import LifecycleNode, Node


def generate_launch_description():
    pkg_odrive = get_package_share_directory("odrive_ros2_pkg")
    namespace = LaunchConfiguration("namespace")
    tf_remappings = [("/tf", "tf"), ("/tf_static", "tf_static")]
    frame_prefix = PythonExpression(["'", namespace, "'.strip('/')"])
    base_link_frame = PathJoinSubstitution([frame_prefix, "base_link"])
    laser_frame = PathJoinSubstitution([frame_prefix, "laser_frame"])

    namespace_argument = DeclareLaunchArgument(
        "namespace",
        default_value="",
        description="ROS namespace used by all Robis nodes, topics, and TF frames.",
    )

    cmd_lidar = LifecycleNode(
        package="ydlidar_ros2_driver",
        executable="ydlidar_ros2_driver_node",
        name="ydlidar_ros2_driver_node",
        namespace=namespace,
        output="screen",
        emulate_tty=True,
        parameters=[
            os.path.join(pkg_odrive, "params", "ydlidar.yaml"),
            {"frame_id": laser_frame},
        ],
    )

    cmd_lidar_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_tf_pub_laser",
        namespace=namespace,
        remappings=tf_remappings,
        arguments=[
            "0",
            "0",
            "0.02",
            "0",
            "0",
            "0",
            "1",
            base_link_frame,
            laser_frame,
        ],
    )

    cmd_odrive = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_odrive, "launch", "odrive_launch.py")
        ),
        launch_arguments={"namespace": namespace}.items(),
    )

    return LaunchDescription(
        [
            namespace_argument,
            cmd_lidar,
            cmd_lidar_tf,
            cmd_odrive,
        ]
    )
