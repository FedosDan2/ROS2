"""Tests for PR04 pure functions."""

import math

from geometry_msgs.msg import Twist
from patrol.patrol import (
    compute_command,
    validate_linear_speed,
    validate_publish_hz,
    validate_turn_rate,
)
import pytest
from turtlesim_msgs.msg import Pose


def test_missing_pose_returns_zero_twist() -> None:
    """Missing pose produces zero command."""
    cmd = compute_command(None)

    assert isinstance(cmd, Twist)

    assert cmd.linear.x == 0.0
    assert cmd.linear.y == 0.0
    assert cmd.linear.z == 0.0

    assert cmd.angular.x == 0.0
    assert cmd.angular.y == 0.0
    assert cmd.angular.z == 0.0


def test_normal_pose_uses_parameters() -> None:
    """Existing pose produces command from parameters."""
    pose = Pose()
    pose.x = 1.0
    pose.y = 2.0
    pose.theta = 0.5

    cmd = compute_command(pose, 0.25, -0.5)

    assert math.isclose(cmd.linear.x, 0.25, abs_tol=1e-9)
    assert math.isclose(cmd.angular.z, -0.5, abs_tol=1e-9)

    assert cmd.linear.y == 0.0
    assert cmd.linear.z == 0.0

    assert cmd.angular.x == 0.0
    assert cmd.angular.y == 0.0


def test_default_parameters_match_pr03_behavior() -> None:
    """Default command keeps PR03 behavior."""
    pose = Pose()
    pose.x = 1.0
    pose.y = 2.0
    pose.theta = 0.5

    cmd = compute_command(pose)

    assert math.isclose(cmd.linear.x, 0.5, abs_tol=1e-9)
    assert math.isclose(cmd.angular.z, 0.3, abs_tol=1e-9)


def test_publish_hz_accepts_normal_change_10_to_5() -> None:
    """Valid frequency values are accepted."""
    assert validate_publish_hz(10.0) == 10.0
    assert validate_publish_hz(5.0) == 5.0


def test_publish_hz_rejects_zero() -> None:
    """Zero frequency must be rejected."""
    with pytest.raises(ValueError):
        validate_publish_hz(0.0)


def test_publish_hz_rejects_negative_value() -> None:
    """Negative frequency must be rejected."""
    with pytest.raises(ValueError):
        validate_publish_hz(-1.0)


def test_publish_hz_rejects_nan() -> None:
    """Nan frequency must be rejected."""
    with pytest.raises(ValueError):
        validate_publish_hz(math.nan)


def test_linear_speed_and_turn_rate_ranges() -> None:
    """Speed and turn parameters respect ranges."""
    assert validate_linear_speed(0.0) == 0.0
    assert validate_linear_speed(1.0) == 1.0

    assert validate_turn_rate(-1.0) == -1.0
    assert validate_turn_rate(1.0) == 1.0

    with pytest.raises(ValueError):
        validate_linear_speed(1.1)

    with pytest.raises(ValueError):
        validate_turn_rate(-1.1)
