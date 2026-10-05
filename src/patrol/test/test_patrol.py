import math

from geometry_msgs.msg import Twist

from patrol.patrol import (
    ANGULAR_Z_MAX,
    ANGULAR_Z_MIN,
    compute_command,
    LINEAR_X_MAX,
    LINEAR_X_MIN,
)

from turtlesim_msgs.msg import Pose


def test_missing_pose_returns_zero_twist():
    cmd = compute_command(None)

    assert isinstance(cmd, Twist)

    assert cmd.linear.x == 0.0
    assert cmd.linear.y == 0.0
    assert cmd.linear.z == 0.0

    assert cmd.angular.x == 0.0
    assert cmd.angular.y == 0.0
    assert cmd.angular.z == 0.0


def test_normal_pose_returns_required_limited_twist():
    pose = Pose()
    pose.x = 1.0
    pose.y = 2.0
    pose.theta = 0.5

    cmd = compute_command(pose)

    assert math.isclose(cmd.linear.x, 0.5, abs_tol=1e-9)
    assert math.isclose(cmd.angular.z, 0.3, abs_tol=1e-9)

    assert cmd.linear.y == 0.0
    assert cmd.linear.z == 0.0

    assert cmd.angular.x == 0.0
    assert cmd.angular.y == 0.0

    assert LINEAR_X_MIN <= cmd.linear.x <= LINEAR_X_MAX
    assert ANGULAR_Z_MIN <= cmd.angular.z <= ANGULAR_Z_MAX
