# Robis ROS 2

The ROS 2 package is in `odrive_ros2_pkg`.

## Build the Docker image

```bash
docker buildx build --platform linux/arm64 --push \
  -t 10.20.5.15:5000/wagnercotta/is-robis-ros2:latest .
```

## Run with Docker

```bash
sudo docker run --rm --privileged -it --network=host \
  -v /dev/bus/usb:/dev/bus/usb \
  --name=robis_ros2 \
  10.20.5.15:5000/wagnercotta/is-robis-ros2:latest
```

The container entrypoint sources ROS 2 and the workspace, then runs:

```bash
ros2 launch odrive_ros2_pkg is_robis_ros2_launch.py namespace:=robis
```

To open a shell instead of launching Robis, override the default command:

```bash
sudo docker run --rm --privileged -it --network=host \
  -v /dev/bus/usb:/dev/bus/usb \
  --name=robis_ros2 \
  10.20.5.15:5000/wagnercotta/is-robis-ros2:latest bash
```
