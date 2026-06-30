import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory("odrive_ros2_pkg")
    return LaunchDescription(
        [
            Node(
                package="odrive_ros2_pkg",
                executable="robis_navigation_server",
                namespace="robis",
                name="robis_navigation_server",
                output="screen",
                emulate_tty=True,
                parameters=[
                    os.path.join(
                        package_share,
                        "params",
                        "robis_navigation.yaml",
                    ),
                    {
                        "use_sim_time": True,
                    }
                ],
            ),
        ]
    )
