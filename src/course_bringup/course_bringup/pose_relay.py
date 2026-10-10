from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from turtlesim_msgs.msg import Pose

PUB_DEPTH = 10
SUB_DEPTH = 10


def build_qos(reliability: str, depth: int) -> QoSProfile:
    if reliability == 'reliable':
        rel = ReliabilityPolicy.RELIABLE
    elif reliability == 'best_effort':
        rel = ReliabilityPolicy.BEST_EFFORT
    else:
        raise ValueError(
            f'reliability must be reliable or best_effort, '
            f'got {reliability!r}'
        )

    return QoSProfile(
        reliability=rel,
        history=HistoryPolicy.KEEP_LAST,
        depth=depth,
    )


class PoseRelay(Node):
    """Reads /turtle1/pose and republishes to relative sensor_pose."""

    def __init__(self) -> None:
        """Initialize relay publisher and configurable listener."""
        super().__init__('pose_relay')

        self.declare_parameter('subscriber_reliability', 'reliable')

        reliability = str(
            self.get_parameter('subscriber_reliability').value
        )

        self.pub_qos = build_qos('best_effort', PUB_DEPTH)
        self.sub_qos = build_qos(reliability, SUB_DEPTH)

        self.source_subscription = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.source_callback,
            10,
        )

        self.relay_publisher = self.create_publisher(
            Pose,
            'sensor_pose',
            self.pub_qos,
        )

        self.listener_subscription = self.create_subscription(
            Pose,
            'sensor_pose',
            self.listener_callback,
            self.sub_qos,
        )

        self.published_count = 0
        self.received_count = 0

        self.get_logger().info(
            f'PoseRelay started: pub=best_effort, sub={reliability}'
        )

    def source_callback(self, msg: Pose) -> None:
        """Forward source pose to relative sensor_pose."""
        self.relay_publisher.publish(msg)
        self.published_count += 1

    def listener_callback(self, msg: Pose) -> None:
        """Count receipt on the configurable listener side."""
        self.received_count += 1
        self.get_logger().info(
            f'Listener received sensor_pose '
            f'#{self.received_count}'
        )


def main(args: Optional[list[str]] = None) -> None:
    """Run pose relay node."""
    rclpy.init(args=args)

    node: Optional[PoseRelay] = None

    try:
        node = PoseRelay()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':
    main()
