"""PR03 patrol node."""

from typing import Optional

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from turtlesim_msgs.msg import Pose

DESIRED_LINEAR_X = 0.5
DESIRED_ANGULAR_Z = 0.3

LINEAR_X_MIN = 0.0
LINEAR_X_MAX = 0.5
ANGULAR_Z_MIN = -1.0
ANGULAR_Z_MAX = 1.0


def clamp(value: float, lower: float, upper: float) -> float:
    """Clamp value to inclusive range."""
    return max(lower, min(upper, value))


def compute_command(pose: Optional[Pose]) -> Twist:
    """Return Twist command for the latest pose."""
    cmd = Twist()

    if pose is None:
        return cmd

    cmd.linear.x = clamp(DESIRED_LINEAR_X, LINEAR_X_MIN, LINEAR_X_MAX)
    cmd.angular.z = clamp(DESIRED_ANGULAR_Z, ANGULAR_Z_MIN, ANGULAR_Z_MAX)

    return cmd


class Patrol(Node):
    """Publishes Twist commands from the latest turtlesim pose."""

    def __init__(self) -> None:
        """Initialize subscription, publisher and timer."""
        super().__init__('patrol')

        self.last_pose: Optional[Pose] = None

        self.subscription = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10,
        )

        self.publisher = self.create_publisher(
            Twist,
            'cmd_vel',
            10,
        )

        self.timer = self.create_timer(0.1, self.timer_callback)

        self.get_logger().info('Patrol started')

    def pose_callback(self, msg: Pose) -> None:
        """Store the latest pose."""
        self.last_pose = msg

    def timer_callback(self) -> None:
        """Publish command computed from the latest pose."""
        cmd = compute_command(self.last_pose)
        self.publisher.publish(cmd)

    def send_zero(self) -> None:
        """Publish zero Twist before shutdown safely."""
        try:
            # Проверяем, что издатель еще жив
            if self.publisher and not self.publisher.is_destroyed():
                self.publisher.publish(Twist())
                self.get_logger().info('Published zero Twist')
        except Exception as e:
            # Игнорируем ошибки при остановке, если контекст уже закрыт
            self.get_logger().debug(f'Shutdown publish error (ignored): {e}')


def main(args: Optional[list[str]] = None) -> None:
    """Run patrol node."""
    rclpy.init(args=args)

    node: Optional[Patrol] = None

    try:
        node = Patrol()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.send_zero()
            node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':
    main()
