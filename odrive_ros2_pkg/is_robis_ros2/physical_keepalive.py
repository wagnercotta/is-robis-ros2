"""Publish the Robis physical keepalive for the IS-Wire ROS gateway."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Empty


class PhysicalKeepalivePublisher(Node):
    """Periodically report that the physical Robis platform is alive."""

    DEFAULT_TOPIC = "/is/Agent/Robot/Robis/PhysicalKeepalive"

    def __init__(self) -> None:
        super().__init__("physical_keepalive_publisher")
        self.declare_parameter("topic", self.DEFAULT_TOPIC)
        self.declare_parameter("period_seconds", 10.0)

        topic = str(self.get_parameter("topic").value).strip()
        period = float(self.get_parameter("period_seconds").value)
        if not topic:
            raise ValueError("The physical keepalive topic cannot be empty")
        if period <= 0.0:
            raise ValueError("period_seconds must be greater than zero")

        self._publisher = self.create_publisher(Empty, topic, 10)
        self._timer = self.create_timer(period, self._publish_keepalive)
        self._publish_keepalive()
        self.get_logger().info(
            f"Publishing physical keepalive on '{topic}' every {period:g}s"
        )

    def _publish_keepalive(self) -> None:
        self._publisher.publish(Empty())


def main(args=None) -> None:
    """Run the physical keepalive publisher node."""
    rclpy.init(args=args)
    node = PhysicalKeepalivePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
