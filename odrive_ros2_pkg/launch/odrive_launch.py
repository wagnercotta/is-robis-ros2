from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    namespace = LaunchConfiguration("namespace")

    namespace_argument = DeclareLaunchArgument(
        "namespace",
        default_value="",
        description="ROS namespace used by the ODrive nodes and TF frames.",
    )

    return LaunchDescription(
        [
            namespace_argument,
            Node(
                package="is_robis_ros2",
                executable="odrive_node",
                name="odrive_node",
                namespace=namespace,
                output="screen",
                emulate_tty=True,
                remappings=[("/tf", "tf"), ("/tf_static", "tf_static")],
                parameters=[
                    {
                        "simulation_mode": False,
                        "wheel_track": 0.35,
                        "tyre_circumference": 0.537,
                        "odom_frame": "odom",
                        "base_frame": "base_link",
                        "publish_odom_tf": False,
                    }
                ],
            ),
        ]
    )
