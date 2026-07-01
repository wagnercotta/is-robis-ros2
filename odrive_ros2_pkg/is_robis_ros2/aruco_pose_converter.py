import json
import math
import threading

import rclpy
from example_interfaces.srv import Trigger
from geometry_msgs.msg import Pose2D, PoseWithCovarianceStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data


class ArucoPoseConverter(Node):
    """Convert planar ArUco poses into covariance-stamped map poses."""

    def __init__(self):
        super().__init__("aruco_pose_converter")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("position_variance", 0.01)
        self.declare_parameter("yaw_variance", 0.02)
        self.declare_parameter("unobserved_variance", 1000000.0)
        self._last_pose = None
        self._pose_lock = threading.Lock()
        self._publisher = self.create_publisher(
            PoseWithCovarianceStamped,
            "aruco_pose",
            qos_profile_sensor_data,
        )
        self.create_subscription(
            Pose2D,
            "ArucoPose",
            self._pose_callback,
            qos_profile_sensor_data,
        )
        self.create_service(Trigger, "get_position", self._get_position)

    def _pose_callback(self, msg):
        x = float(msg.x)
        y = float(msg.y)
        yaw = float(msg.theta)
        with self._pose_lock:
            self._last_pose = (x, y, yaw)

        output = PoseWithCovarianceStamped()
        output.header.stamp = self.get_clock().now().to_msg()
        output.header.frame_id = self.get_parameter("map_frame").value
        output.pose.pose.position.x = x
        output.pose.pose.position.y = y
        output.pose.pose.orientation.z = math.sin(yaw / 2.0)
        output.pose.pose.orientation.w = math.cos(yaw / 2.0)
        position_variance = float(
            self.get_parameter("position_variance").value
        )
        yaw_variance = float(self.get_parameter("yaw_variance").value)
        unobserved_variance = float(
            self.get_parameter("unobserved_variance").value
        )
        output.pose.covariance[0] = position_variance
        output.pose.covariance[7] = position_variance
        output.pose.covariance[14] = unobserved_variance
        output.pose.covariance[21] = unobserved_variance
        output.pose.covariance[28] = unobserved_variance
        output.pose.covariance[35] = yaw_variance
        self._publisher.publish(output)

    def _get_position(self, _request, response):
        with self._pose_lock:
            pose = self._last_pose
        if pose is None:
            response.success = False
            response.message = json.dumps({"error": "position_unavailable"})
            return response
        response.success = True
        response.message = json.dumps(
            {"x": pose[0], "y": pose[1], "z": 0.0, "yaw": pose[2]}
        )
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ArucoPoseConverter()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        try:
            node.destroy_node()
        finally:
            if rclpy.ok():
                rclpy.shutdown()


if __name__ == "__main__":
    main()
