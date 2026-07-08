# Robis ROS 2

The ROS 2 package is in `odrive_ros2_pkg` and is installed as
`is_robis_ros2`.

## Build the Docker image

```bash
docker buildx build --platform linux/arm64 --push \
  -f etc/docker/Dockerfile \
  -t 10.20.5.15:5000/wagnercotta/is-robis-ros2:latest .
```

## Run with Docker

```bash
sudo docker run --rm --privileged -it --network=host \
  -v /dev/bus/usb:/dev/bus/usb \
  -e ROBOT_NAMESPACE=robis \
  --name=robis_ros2 \
  10.20.5.15:5000/wagnercotta/is-robis-ros2:latest
```

The container entrypoint sources ROS 2 and the workspace, then runs:

```bash
ros2 launch is_robis_ros2 is_robis_ros2_launch.py namespace:=<robot_namespace>
```

The launch starts the ODrive driver, lidar, ArUco pose converter, physical
keepalive publisher, `robot_localization`, map server, and Nav2. Its default map is
`map_cam_odom_exp_170601.yaml`. The local EKF publishes `odom` to
`base_link`, while the global EKF uses the ArUco pose to publish `map` to
`odom`. AMCL is not started.

The physical keepalive publishes `std_msgs/msg/Empty` every 10 seconds on
`/is/Agent/Robot/Robis/PhysicalKeepalive`. The ROS 2 gateway forwards it as
`google.protobuf.Empty` to `Agent.Robot.Robis.PhysicalKeepalive`.

The image defaults `ROBOT_NAMESPACE` to `robis`. Override it with Docker's
`-e ROBOT_NAMESPACE=<namespace>` option when needed.

To open a shell instead of launching Robis, override the default command:

```bash
sudo docker run --rm --privileged -it --network=host \
  -v /dev/bus/usb:/dev/bus/usb \
  --name=robis_ros2 \
  10.20.5.15:5000/wagnercotta/is-robis-ros2:latest bash
```
