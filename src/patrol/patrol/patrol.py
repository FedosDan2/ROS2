"""PR04 patrol node with runtime parameters."""

import math
from typing import Optional

from geometry_msgs.msg import Twist
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from turtlesim_msgs.msg import Pose

DEFAULT_LINEAR_SPEED = 0.5
DEFAULT_TURN_RATE = 0.3
DEFAULT_PUBLISH_HZ = 10.0

LINEAR_SPEED_MIN = 0.0
LINEAR_SPEED_MAX = 1.0
TURN_RATE_MIN = -1.0
TURN_RATE_MAX = 1.0
PUBLISH_HZ_MIN = 1.0
PUBLISH_HZ_MAX = 30.0


def clamp(value: float, lower: float, upper: float) -> float:
    """Clamp value to inclusive range."""
    return max(lower, min(upper, value))


def validate_finite_range(
    value: float,
    name: str,
    lower: float,
    upper: float,
) -> float:
    """Validate that value is finite and inside inclusive range."""
    number = float(value)

    if not math.isfinite(number):
        raise ValueError(f'{name} must be finite')

    if number < lower or number > upper:
        raise ValueError(
            f'{name} must be in [{lower}, {upper}]'
        )

    return number


def validate_linear_speed(value: float) -> float:
    """Validate linear_speed parameter."""
    return validate_finite_range(
        value,
        'linear_speed',
        LINEAR_SPEED_MIN,
        LINEAR_SPEED_MAX,
    )


def validate_turn_rate(value: float) -> float:
    """Validate turn_rate parameter."""
    return validate_finite_range(
        value,
        'turn_rate',
        TURN_RATE_MIN,
        TURN_RATE_MAX,
    )


def validate_publish_hz(value: float) -> float:
    """Validate publish_hz parameter."""
    return validate_finite_range(
        value,
        'publish_hz',
        PUBLISH_HZ_MIN,
        PUBLISH_HZ_MAX,
    )


def validate_all(
    linear_speed: float,
    turn_rate: float,
    publish_hz: float,
) -> tuple[float, float, float]:
    """Validate all patrol parameters."""
    return (
        validate_linear_speed(linear_speed),
        validate_turn_rate(turn_rate),
        validate_publish_hz(publish_hz),
    )


def compute_command(
    pose: Optional[Pose],
    linear_speed: float = DEFAULT_LINEAR_SPEED,
    turn_rate: float = DEFAULT_TURN_RATE,
) -> Twist:
    """Return Twist command for the latest pose and parameters."""
    cmd = Twist()

    if pose is None:
        return cmd

    cmd.linear.x = clamp(
        linear_speed,
        LINEAR_SPEED_MIN,
        LINEAR_SPEED_MAX,
    )

    cmd.angular.z = clamp(
        turn_rate,
        TURN_RATE_MIN,
        TURN_RATE_MAX,
    )

    return cmd


class Patrol(Node):
    """Publishes Twist commands from the latest turtlesim pose."""

    def __init__(self) -> None:
        """Initialize parameters, subscription, publisher and timer."""
        super().__init__('patrol')

        self.last_pose: Optional[Pose] = None

        self.linear_speed = DEFAULT_LINEAR_SPEED
        self.turn_rate = DEFAULT_TURN_RATE
        self.publish_hz = DEFAULT_PUBLISH_HZ

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

        self.declare_parameter('linear_speed', DEFAULT_LINEAR_SPEED)
        self.declare_parameter('turn_rate', DEFAULT_TURN_RATE)
        self.declare_parameter('publish_hz', DEFAULT_PUBLISH_HZ)

        self.linear_speed, self.turn_rate, self.publish_hz = validate_all(
            float(self.get_parameter('linear_speed').value),
            float(self.get_parameter('turn_rate').value),
            float(self.get_parameter('publish_hz').value),
        )

        self.timer = self.create_timer(
            1.0 / self.publish_hz,
            self.timer_callback,
        )

        self.add_on_set_parameters_callback(self._on_set_parameters)

        self.get_logger().info(
            f'Patrol started at {self.publish_hz:.3f} Hz'
        )

    def pose_callback(self, msg: Pose) -> None:
        """Store the latest pose."""
        self.last_pose = msg

    def timer_callback(self) -> None:
        """Publish command computed from latest pose and parameters."""
        cmd = compute_command(
            self.last_pose,
            self.linear_speed,
            self.turn_rate,
        )

        self.publisher.publish(cmd)

    def _restart_timer(self, publish_hz: float) -> None:
        """Replace active timer with a new period."""
        self.timer.cancel()

        self.timer = self.create_timer(
            1.0 / publish_hz,
            self.timer_callback,
        )

        self.get_logger().info(
            f'Timer restarted at {publish_hz:.3f} Hz'
        )

    def _on_set_parameters(
        self,
        parameters: list[Parameter],
    ) -> SetParametersResult:
        """Validate parameters before changing active state."""
        validated: dict[str, float] = {}
        new_publish_hz: Optional[float] = None

        for param in parameters:
            if param.name not in {
                'linear_speed',
                'turn_rate',
                'publish_hz',
            }:
                continue

            try:
                number = float(param.value)
            except (TypeError, ValueError) as exc:
                return SetParametersResult(
                    successful=False,
                    reason=(
                        f'{param.name}: expected number ({exc})'
                    ),
                )

            try:
                if param.name == 'linear_speed':
                    validated[param.name] = validate_linear_speed(number)

                elif param.name == 'turn_rate':
                    validated[param.name] = validate_turn_rate(number)

                else:
                    validated[param.name] = validate_publish_hz(number)
                    new_publish_hz = validated[param.name]

            except ValueError as exc:
                return SetParametersResult(
                    successful=False,
                    reason=str(exc),
                )

        for name, value in validated.items():
            setattr(self, name, value)

        if new_publish_hz is not None:
            self._restart_timer(new_publish_hz)

        return SetParametersResult(successful=True)

    def send_zero(self) -> None:
        """Publish zero Twist before shutdown safely."""
        try:
            self.publisher.publish(Twist())
            self.get_logger().info('Published zero Twist')
        except Exception as exc:
            self.get_logger().debug(
                f'Shutdown publish error ignored: {exc}'
            )


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
