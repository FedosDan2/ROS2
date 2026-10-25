
import math
from typing import Tuple

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from rclpy.time import Time

from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import Twist, Vector3


def convert_to_twist(
    speed: float,
    steering_angle: float,
    current_sim_time_sec: float,
    msg_stamp_sec: float,
    wheelbase: float = 0.8
) -> Tuple[Twist, str]:
    """
    Pure function to convert Ackermann command to Twist.
    
    Returns:
        Tuple of (Twist message, error_reason). 
        If error_reason is not empty, the Twist is zeroed.
    """
    # 1. Проверка на NaN или Inf
    if not math.isfinite(speed) or not math.isfinite(steering_angle):
        return Twist(), "NaN or Inf detected in command"
    
    # 2. Проверка на устаревание команды (> 0.25 с)
    age = current_sim_time_sec - msg_stamp_sec
    if age > 0.25:
        return Twist(), f"Command is stale (age: {age:.3f} s > 0.25 s)"
    
    # 3. Ограничение (Clamping)
    v = max(0.0, min(1.2, speed))
    delta = max(-0.45, min(0.45, steering_angle))
    
    # 4. Кинематика Аккермана: angular.z = v * tan(delta) / L
    angular_z = (v * math.tan(delta)) / wheelbase
    
    # 5. Формируем валидное сообщение
    twist = Twist()
    twist.linear.x = float(v)
    twist.angular.z = float(angular_z)
    
    return twist, ""


class AckermannAdapter(Node):
    """ROS 2 Node that adapts safe drive commands for Gazebo."""

    def __init__(self) -> None:
        super().__init__('ackermann_adapter')
        
        # QoS профиль: надежная доставка для команд управления
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.subscription = self.create_subscription(
            AckermannDriveStamped,
            '/drive/safe',
            self.drive_callback,
            qos
        )
        
        self.publisher = self.create_publisher(
            Twist,
            '/vehicle/gz_cmd_vel',
            qos
        )
        
        self.get_logger().info('AckermannAdapter initialized and waiting for commands.')

    def drive_callback(self, msg: AckermannDriveStamped) -> None:
        """Process incoming safe drive command."""
        current_time = self.get_clock().now()
        msg_time = Time.from_msg(msg.header.stamp)
        
        current_sec = current_time.nanoseconds / 1e9
        msg_sec = msg_time.nanoseconds / 1e9
        
        twist, error_reason = convert_to_twist(
            speed=msg.drive.speed,
            steering_angle=msg.drive.steering_angle,
            current_sim_time_sec=current_sec,
            msg_stamp_sec=msg_sec
        )
        
        if error_reason:
            self.get_logger().warning(f"Publishing ZERO command: {error_reason}")
        
        self.publisher.publish(twist)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = AckermannAdapter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()