import math
import pytest
from geometry_msgs.msg import Twist

from course_simulation.ackermann_adapter import convert_to_twist


def test_straight_motion() -> None:
    """Test straight motion: speed=0.5, angle=0.0."""
    twist, err = convert_to_twist(0.5, 0.0, 10.0, 10.0)
    assert err == ""
    assert twist.linear.x == pytest.approx(0.5)
    assert twist.angular.z == pytest.approx(0.0)


def test_turning_motion() -> None:
    """Test turning: speed=0.5, angle=0.2 rad."""
    twist, err = convert_to_twist(0.5, 0.2, 10.0, 10.0)
    assert err == ""
    assert twist.linear.x == pytest.approx(0.5)
    # angular.z = 0.5 * tan(0.2) / 0.8
    expected_angular = (0.5 * math.tan(0.2)) / 0.8
    assert twist.angular.z == pytest.approx(expected_angular)


def test_zero_speed() -> None:
    """Test zero speed: car should not rotate in place."""
    twist, err = convert_to_twist(0.0, 0.4, 10.0, 10.0)
    assert err == ""
    assert twist.linear.x == pytest.approx(0.0)
    assert twist.angular.z == pytest.approx(0.0)


def test_clamping_speed_and_angle() -> None:
    """Test that speed and angle are clamped to max limits."""
    # speed=2.0 -> clamped to 1.2, angle=1.0 -> clamped to 0.45
    twist, err = convert_to_twist(2.0, 1.0, 10.0, 10.0)
    assert err == ""
    assert twist.linear.x == pytest.approx(1.2)
    assert twist.angular.z == pytest.approx((1.2 * math.tan(0.45)) / 0.8)


def test_nan_speed() -> None:
    """Test that NaN speed results in zero twist and error."""
    twist, err = convert_to_twist(float('nan'), 0.0, 10.0, 10.0)
    assert "NaN or Inf" in err
    assert twist.linear.x == 0.0
    assert twist.angular.z == 0.0


def test_inf_steering() -> None:
    """Test that Inf steering results in zero twist and error."""
    twist, err = convert_to_twist(0.5, float('inf'), 10.0, 10.0)
    assert "NaN or Inf" in err
    assert twist.linear.x == 0.0
    assert twist.angular.z == 0.0


def test_stale_command() -> None:
    """Test that command older than 0.25s is rejected."""
    # current time = 10.5, msg time = 10.0 -> age = 0.5s > 0.25s
    twist, err = convert_to_twist(0.5, 0.0, 10.5, 10.0)
    assert "stale" in err.lower()
    assert twist.linear.x == 0.0
    assert twist.angular.z == 0.0


def test_fresh_command() -> None:
    """Test that command younger than 0.25s is accepted."""
    # current time = 10.2, msg time = 10.0 -> age = 0.2s < 0.25s
    twist, err = convert_to_twist(0.5, 0.0, 10.2, 10.0)
    assert err == ""
    assert twist.linear.x == pytest.approx(0.5)