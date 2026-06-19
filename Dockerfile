FROM ros:humble

RUN apt update
RUN apt install -y usbutils net-tools software-properties-common wget
RUN apt-get install -y libjpeg-dev libjpeg8-dev libfreetype6-dev vim

RUN wget https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py
RUN python3 -m pip install --upgrade odrive

RUN apt-get install -y ros-humble-diagnostic-updater
RUN apt-get install -y ros-humble-tf-transformations
#RUN apt install -y ros-humble-slam-toolbox

WORKDIR /workspace/ros2_ws
RUN mkdir -p src
COPY odrive_ros2_pkg/ src/odrive_ros2_pkg/

WORKDIR /workspace/ros2_ws
RUN colcon build --packages-select odrive_ros2_pkg

SHELL [ "/bin/bash" , "-c" ]

# Lidar
RUN apt install cmake pkg-config

WORKDIR /workspace

RUN git clone https://github.com/matheusdutra0207/YDLidar-SDK.git
WORKDIR /workspace/YDLidar-SDK/build
RUN cmake ..
RUN make
RUN make install
RUN cpack

WORKDIR /workspace/ros2_ws

RUN cd src/ \
    && git clone -b humble https://github.com/matheusdutra0207/ydlidar_ros2_driver.git \
    && cd .. \
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

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["ros2", "launch", "odrive_ros2_pkg", "is_robis_ros2_launch.py", "namespace:=robis"]

WORKDIR /workspace/ros2_ws
