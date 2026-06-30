import json
import math
import threading
import time

import rclpy
from example_interfaces.srv import Trigger
from geometry_msgs.msg import Pose2D, Twist
from nav2_msgs.action import NavigateThroughPoses, NavigateToPose
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import Float32MultiArray


class RobisNavigationServer(Node):
    """Expose Robis navigation operations backed exclusively by cmd_vel."""

    def __init__(self):
        super().__init__("robis_navigation_server")
        self.declare_parameter("kp_linear", 0.3)
        self.declare_parameter("kp_angular", 2.0)
        self.declare_parameter("avoidance_gain", 1.5)
        self.declare_parameter("max_linear_speed", 0.6)
        self.declare_parameter("max_angular_speed", 2.0)
        self.declare_parameter("goal_tolerance", 0.05)
        self.declare_parameter("control_rate_hz", 50.0)
        self.declare_parameter("pose_timeout_seconds", 10.0)
        self.declare_parameter("goal_timeout_seconds", 60.0)
        self.declare_parameter("avoidance_timeout_seconds", 0.5)

        self._pose = None
        self._pose_lock = threading.Lock()
        self._avoidance = (0.0, 0.0)
        self._avoidance_updated_at = None
        self._avoidance_lock = threading.Lock()
        self._execution_lock = threading.Lock()
        self._active_cancel = None
        self._active_cancel_lock = threading.Lock()
        callback_group = ReentrantCallbackGroup()

        self.create_subscription(
            Pose2D,
            "/robis/ArucoPose",
            self._pose_callback,
            qos_profile_sensor_data,
            callback_group=callback_group,
        )
        self.create_subscription(
            Float32MultiArray,
            "/desvio_potencial",
            self._avoidance_callback,
            10,
            callback_group=callback_group,
        )
        self._cmd_vel = self.create_publisher(Twist, "cmd_vel", 10)
        self._navigate_to_pose = ActionServer(
            self,
            NavigateToPose,
            "navigate_to_pose",
            execute_callback=self._execute_navigate_to_pose,
            goal_callback=self._goal_callback,
            cancel_callback=self._cancel_callback,
            callback_group=callback_group,
        )
        self._follow_trajectory = ActionServer(
            self,
            NavigateThroughPoses,
            "follow_trajectory",
            execute_callback=self._execute_follow_trajectory,
            goal_callback=self._trajectory_goal_callback,
            cancel_callback=self._cancel_callback,
            callback_group=callback_group,
        )
        self._cancel_service = self.create_service(
            Trigger,
            "cancel_navigation",
            self._cancel_navigation,
            callback_group=callback_group,
        )
        self._position_service = self.create_service(
            Trigger,
            "get_position",
            self._get_position,
            callback_group=callback_group,
        )
        self.get_logger().info(
            "Robis navigation ready: navigate_to_pose, follow_trajectory, "
            "cancel_navigation and get_position; output=/robis/cmd_vel"
        )

    @staticmethod
    def _clamp(value, lower, upper):
        return max(lower, min(upper, value))

    def _parameter(self, name):
        return self.get_parameter(name).value

    def _pose_callback(self, msg):
        with self._pose_lock:
            self._pose = (float(msg.x), float(msg.y), float(msg.theta))

    def _avoidance_callback(self, msg):
        if len(msg.data) < 2:
            return
        with self._avoidance_lock:
            self._avoidance = (float(msg.data[0]), float(msg.data[1]))
            self._avoidance_updated_at = time.monotonic()

    def _current_pose(self):
        with self._pose_lock:
            return self._pose

    def _publish_stop(self):
        self._cmd_vel.publish(Twist())

    def _goal_callback(self, _goal_request):
        return GoalResponse.ACCEPT

    def _trajectory_goal_callback(self, goal_request):
        if not goal_request.poses:
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def _cancel_callback(self, _goal_handle):
        with self._active_cancel_lock:
            if self._active_cancel is not None:
                self._active_cancel.set()
        return CancelResponse.ACCEPT

    def _cancel_navigation(self, _request, response):
        with self._active_cancel_lock:
            active_cancel = self._active_cancel
        if active_cancel is not None:
            active_cancel.set()
        self._publish_stop()
        response.success = True
        response.message = "Navigation cancellation requested"
        return response

    def _get_position(self, _request, response):
        pose = self._current_pose()
        if pose is None:
            response.success = False
            response.message = json.dumps({"error": "position_unavailable"})
            return response
        response.success = True
        response.message = json.dumps(
            {"x": pose[0], "y": pose[1], "z": 0.0, "yaw": pose[2]}
        )
        return response

    def _command(self, pose, target_x, target_y):
        x, y, yaw = pose
        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy)
        target_yaw = math.atan2(dy, dx)
        yaw_error = math.atan2(
            math.sin(target_yaw - yaw),
            math.cos(target_yaw - yaw),
        )
        linear = self._parameter("kp_linear") * distance * math.cos(yaw_error)
        angular = self._parameter("kp_angular") * yaw_error

        with self._avoidance_lock:
            vx_global, vy_global = self._avoidance
            updated_at = self._avoidance_updated_at
        if (
            updated_at is None
            or time.monotonic() - updated_at
            > self._parameter("avoidance_timeout_seconds")
        ):
            vx_global = 0.0
            vy_global = 0.0
        vx_local = vx_global * math.cos(yaw) + vy_global * math.sin(yaw)
        vy_local = -vx_global * math.sin(yaw) + vy_global * math.cos(yaw)

        command = Twist()
        command.linear.x = self._clamp(
            linear + vx_local,
            -self._parameter("max_linear_speed"),
            self._parameter("max_linear_speed"),
        )
        command.angular.z = self._clamp(
            angular + self._parameter("avoidance_gain") * vy_local,
            -self._parameter("max_angular_speed"),
            self._parameter("max_angular_speed"),
        )
        return command, distance

    @staticmethod
    def _fill_pose_stamped(message, pose, stamp):
        message.header.frame_id = "map"
        message.header.stamp = stamp
        message.pose.position.x = pose[0]
        message.pose.position.y = pose[1]
        half_yaw = pose[2] / 2.0
        message.pose.orientation.z = math.sin(half_yaw)
        message.pose.orientation.w = math.cos(half_yaw)

    def _track_target(
        self,
        goal_handle,
        cancel_event,
        target_x,
        target_y,
        feedback_callback,
    ):
        started_at = time.monotonic()
        pose_deadline = started_at + self._parameter("pose_timeout_seconds")
        period = 1.0 / self._parameter("control_rate_hz")
        while rclpy.ok():
            if goal_handle.is_cancel_requested:
                return "cancelled"
            if cancel_event.is_set():
                return "aborted"
            pose = self._current_pose()
            now = time.monotonic()
            if pose is None:
                if now >= pose_deadline:
                    return "pose_unavailable"
                time.sleep(min(period, 0.1))
                continue
            if now - started_at > self._parameter("goal_timeout_seconds"):
                return "timeout"

            command, distance = self._command(pose, target_x, target_y)
            feedback_callback(pose, distance)
            if distance <= self._parameter("goal_tolerance"):
                return "completed"
            self._cmd_vel.publish(command)
            time.sleep(period)
        return "shutdown"

    def _begin_execution(self):
        cancel_event = threading.Event()
        with self._active_cancel_lock:
            previous = self._active_cancel
            self._active_cancel = cancel_event
        if previous is not None:
            previous.set()
        return cancel_event

    def _finish_execution(self, cancel_event):
        with self._active_cancel_lock:
            if self._active_cancel is cancel_event:
                self._active_cancel = None
        self._publish_stop()

    @staticmethod
    def _finish_goal(goal_handle, status):
        if status == "completed":
            goal_handle.succeed()
        elif status == "cancelled":
            goal_handle.canceled()
        else:
            goal_handle.abort()

    def _execute_navigate_to_pose(self, goal_handle):
        with self._execution_lock:
            cancel_event = self._begin_execution()
            target = goal_handle.request.pose.pose.position

            def publish_feedback(pose, distance):
                feedback = NavigateToPose.Feedback()
                self._fill_pose_stamped(
                    feedback.current_pose,
                    pose,
                    self.get_clock().now().to_msg(),
                )
                feedback.distance_remaining = distance
                goal_handle.publish_feedback(feedback)

            try:
                status = self._track_target(
                    goal_handle,
                    cancel_event,
                    float(target.x),
                    float(target.y),
                    publish_feedback,
                )
                self._finish_goal(goal_handle, status)
                return NavigateToPose.Result()
            finally:
                self._finish_execution(cancel_event)

    def _execute_follow_trajectory(self, goal_handle):
        with self._execution_lock:
            cancel_event = self._begin_execution()
            poses = goal_handle.request.poses
            status = "completed"
            try:
                for index, target_pose in enumerate(poses):
                    target = target_pose.pose.position

                    def publish_feedback(pose, distance, point_index=index):
                        feedback = NavigateThroughPoses.Feedback()
                        self._fill_pose_stamped(
                            feedback.current_pose,
                            pose,
                            self.get_clock().now().to_msg(),
                        )
                        feedback.distance_remaining = distance
                        feedback.number_of_poses_remaining = len(poses) - point_index
                        goal_handle.publish_feedback(feedback)

                    status = self._track_target(
                        goal_handle,
                        cancel_event,
                        float(target.x),
                        float(target.y),
                        publish_feedback,
                    )
                    if status != "completed":
                        break
                self._finish_goal(goal_handle, status)
                return NavigateThroughPoses.Result()
            finally:
                self._finish_execution(cancel_event)


def main(args=None):
    rclpy.init(args=args)
    node = RobisNavigationServer()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
