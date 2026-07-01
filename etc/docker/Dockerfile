# syntax=docker/dockerfile:1.7

FROM ros:humble

ENV DEBIAN_FRONTEND=noninteractive \
    RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    ROBOT_NAMESPACE=robis

SHELL ["/bin/bash", "-c"]

# Keep system and ROS dependencies ahead of local source code so application
# changes do not invalidate these expensive layers.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        libfreetype6-dev \
        libjpeg-dev \
        net-tools \
        pkg-config \
        python3-pip \
        ros-humble-diagnostic-updater \
        ros-humble-example-interfaces \
        ros-humble-nav2-bringup \
        ros-humble-rmw-cyclonedds-cpp \
        ros-humble-robot-localization \
        ros-humble-tf-transformations \
        usbutils \
        vim

RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m pip install odrive==0.6.11.post0

# Build third-party lidar dependencies before copying the frequently changing
# Robis package. Docker can then reuse these layers across normal development.
WORKDIR /workspace
RUN git clone --depth 1 https://github.com/matheusdutra0207/YDLidar-SDK.git \
    && cmake -S YDLidar-SDK -B YDLidar-SDK/build \
    && cmake --build YDLidar-SDK/build --parallel "$(nproc)" \
    && cmake --install YDLidar-SDK/build

WORKDIR /workspace/ros2_ws
RUN mkdir -p src \
    && git clone --depth 1 --branch humble \
        https://github.com/matheusdutra0207/ydlidar_ros2_driver.git \
        src/ydlidar_ros2_driver \
    && source /opt/ros/humble/setup.bash \
    && colcon build --packages-select ydlidar_ros2_driver

RUN printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -e' \
    '' \
    'source /opt/ros/humble/setup.bash' \
    '' \
    'if [ -f /workspace/ros2_ws/install/setup.bash ]; then' \
    '    source /workspace/ros2_ws/install/setup.bash' \
    'fi' \
    '' \
    'exec "$@"' \
    > /ros_entrypoint.sh \
    && chmod +x /ros_entrypoint.sh

# This is intentionally the final build layer. Editing local launch files,
# parameters, or Python nodes now rebuilds only this package.
COPY odrive_ros2_pkg/ src/is_robis_ros2/
RUN source /opt/ros/humble/setup.bash \
    && source install/setup.bash \
    && colcon build --packages-select is_robis_ros2

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["/bin/bash", "-lc", "exec ros2 launch is_robis_ros2 is_robis_ros2_launch.py namespace:=\"${ROBOT_NAMESPACE}\""]
