import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node, PushRosNamespace
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    package_share = get_package_share_directory("is_robis_ros2")
    nav2_share = get_package_share_directory("nav2_bringup")

    namespace = LaunchConfiguration("namespace")
    use_sim_time = LaunchConfiguration("use_sim_time")
    map_file = LaunchConfiguration("map")
    nav2_params = LaunchConfiguration("nav2_params")
    ekf_local_params = LaunchConfiguration("ekf_local_params")
    ekf_global_params = LaunchConfiguration("ekf_global_params")
    configured_nav2_params = RewrittenYaml(
        source_file=nav2_params,
        root_key=namespace,
        param_rewrites={
            "use_sim_time": use_sim_time,
            "yaml_filename": map_file,
        },
        convert_types=True,
    )
    launch_arguments = [
        DeclareLaunchArgument(
            "namespace",
            default_value="",
            description="Namespace applied to every robot node and topic.",
        ),
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument(
            "map",
            default_value=os.path.join(
                package_share,
                "maps",
                "map_cam_odom_exp_170601.yaml",
            ),
        ),
        DeclareLaunchArgument(
            "nav2_params",
            default_value=os.path.join(
                package_share,
                "params",
                "nav2_params.yaml",
            ),
        ),
        DeclareLaunchArgument(
            "ekf_local_params",
            default_value=os.path.join(
                package_share,
                "params",
                "ekf_local.yaml",
            ),
        ),
        DeclareLaunchArgument(
            "ekf_global_params",
            default_value=os.path.join(
                package_share,
                "params",
                "ekf_global.yaml",
            ),
        ),
    ]

    lidar = Node(
        package="ydlidar_ros2_driver",
        executable="ydlidar_ros2_driver_node",
        name="ydlidar_ros2_driver_node",
        namespace=namespace,
        output="screen",
        emulate_tty=True,
        parameters=[
            os.path.join(package_share, "params", "ydlidar.yaml"),
            {"frame_id": "laser_frame", "use_sim_time": use_sim_time},
        ],
    )
    lidar_transform = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_tf_pub_laser",
        namespace=namespace,
        arguments=[
            "0",
            "0",
            "0.02",
            "0",
            "0",
            "0",
            "1",
            "base_link",
            "laser_frame",
        ],
        remappings=[("/tf", "tf"), ("/tf_static", "tf_static")],
    )
    odrive = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_share, "launch", "odrive_launch.py")
        ),
        launch_arguments={"namespace": namespace}.items(),
    )
    aruco_converter = Node(
        package="is_robis_ros2",
        executable="aruco_pose_converter",
        name="aruco_pose_converter",
        namespace=namespace,
        output="screen",
        parameters=[{"use_sim_time": use_sim_time, "map_frame": "map"}],
    )
    ekf_local = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node",
        namespace=namespace,
        output="screen",
        parameters=[ekf_local_params, {"use_sim_time": use_sim_time}],
        remappings=[
            ("odometry/filtered", "odometry/local"),
            ("/tf", "tf"),
            ("/tf_static", "tf_static"),
        ],
    )
    ekf_global = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_global_node",
        namespace=namespace,
        output="screen",
        parameters=[ekf_global_params, {"use_sim_time": use_sim_time}],
        remappings=[
            ("odometry/filtered", "odometry/global"),
            ("/tf", "tf"),
            ("/tf_static", "tf_static"),
        ],
    )
    map_server = LifecycleNode(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        namespace=namespace,
        output="screen",
        parameters=[configured_nav2_params],
    )
    map_lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_map",
        namespace=namespace,
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "autostart": True,
                "node_names": ["map_server"],
            }
        ],
    )
    navigation = GroupAction(
        actions=[
            PushRosNamespace(namespace),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        nav2_share,
                        "launch",
                        "navigation_launch.py",
                    )
                ),
                launch_arguments={
                    "namespace": namespace,
                    "use_sim_time": use_sim_time,
                    "autostart": "true",
                    "params_file": nav2_params,
                    "use_composition": "False",
                }.items(),
            ),
        ]
    )
    return LaunchDescription(
        launch_arguments
        + [
            lidar,
            lidar_transform,
            odrive,
            aruco_converter,
            ekf_local,
            ekf_global,
            map_server,
            map_lifecycle_manager,
            navigation,
        ]
    )
