
from typing import Tuple

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


def normalize_odometry(raw_odom: Odometry) -> Tuple[Odometry, TransformStamped]:
    # 1. Нормализуем сообщение Odometry
    norm_odom = Odometry()
    
    # Копируем stamp, но меняем frame_id
    norm_odom.header = raw_odom.header
    norm_odom.header.frame_id = "odom"
    norm_odom.child_frame_id = "base_link"
    
    # Копируем данные pose, twist и ковариации без изменений
    norm_odom.pose = raw_odom.pose
    norm_odom.twist = raw_odom.twist
    norm_odom.pose.covariance = raw_odom.pose.covariance
    norm_odom.twist.covariance = raw_odom.twist.covariance

    # 2. Формируем сообщение TransformStamped для TF (odom -> base_link)
    tf_msg = TransformStamped()
    tf_msg.header = norm_odom.header  # stamp и frame_id = "odom"
    tf_msg.child_frame_id = "base_link"
    
    # Копируем позицию и ориентацию из pose
    tf_msg.transform.translation.x = raw_odom.pose.pose.position.x
    tf_msg.transform.translation.y = raw_odom.pose.pose.position.y
    tf_msg.transform.translation.z = raw_odom.pose.pose.position.z
    tf_msg.transform.rotation = raw_odom.pose.pose.orientation

    return norm_odom, tf_msg


class OdomAdapter(Node):
    """ROS 2 Node that normalizes Gazebo odometry and publishes TF."""

    def __init__(self) -> None:
        super().__init__('odom_adapter')
        
        # QoS профиль: надежная доставка для одометрии
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.subscription = self.create_subscription(
            Odometry,
            '/vehicle/odom_gz',  # Сырой топик от моста
            self.odom_callback,
            qos
        )
        
        self.publisher = self.create_publisher(
            Odometry,
            '/vehicle/odom',     # Нормализованный топик
            qos
        )
        
        self.tf_broadcaster = TransformBroadcaster(self)
        
        self.get_logger().info('OdomAdapter initialized. Waiting for raw odometry...')

    def odom_callback(self, msg: Odometry) -> None:
        """Process incoming raw odometry."""
        norm_odom, tf_msg = normalize_odometry(msg)
        
        self.publisher.publish(norm_odom)
        self.tf_broadcaster.sendTransform(tf_msg)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = OdomAdapter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()