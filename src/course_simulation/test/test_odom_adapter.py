"""Unit tests for the Odom adapter normalization logic."""

import pytest
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Pose, PoseWithCovariance, TwistWithCovariance

from course_simulation.odom_adapter import normalize_odometry


def create_raw_odom() -> Odometry:
    """Helper to create a raw odometry message with Gazebo frames."""
    msg = Odometry()
    msg.header.frame_id = "course_ackermann/odom"
    msg.child_frame_id = "course_ackermann/base_link"
    msg.pose.pose.position.x = 1.0
    msg.pose.pose.position.y = 2.0
    msg.pose.pose.position.z = 0.0
    msg.pose.pose.orientation.w = 1.0
    return msg


def test_frame_normalization() -> None:
    """Test that frames are correctly normalized."""
    raw = create_raw_odom()
    norm_odom, tf_msg = normalize_odometry(raw)
    
    assert norm_odom.header.frame_id == "odom"
    assert norm_odom.child_frame_id == "base_link"
    assert tf_msg.header.frame_id == "odom"
    assert tf_msg.child_frame_id == "base_link"


def test_data_preservation() -> None:
    """Test that pose data is correctly copied to TF and Odometry."""
    raw = create_raw_odom()
    norm_odom, tf_msg = normalize_odometry(raw)
    
    # Проверка Odometry
    assert norm_odom.pose.pose.position.x == pytest.approx(1.0)
    assert norm_odom.pose.pose.position.y == pytest.approx(2.0)
    
    # Проверка TF
    assert tf_msg.transform.translation.x == pytest.approx(1.0)
    assert tf_msg.transform.translation.y == pytest.approx(2.0)
    assert tf_msg.transform.rotation.w == pytest.approx(1.0)


def test_stamp_preservation() -> None:
    """Test that timestamp is preserved."""
    raw = create_raw_odom()
    raw.header.stamp.sec = 123
    raw.header.stamp.nanosec = 456
    
    norm_odom, tf_msg = normalize_odometry(raw)
    
    assert norm_odom.header.stamp.sec == 123
    assert tf_msg.header.stamp.sec == 123