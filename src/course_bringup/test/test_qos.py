from course_bringup.pose_relay import build_qos
import pytest
from rclpy.qos import ReliabilityPolicy


def test_build_qos_reliable() -> None:
    """Reliable string maps to RELIABLE policy."""
    qos = build_qos('reliable', 10)
    assert qos.reliability == ReliabilityPolicy.RELIABLE
    assert qos.depth == 10


def test_build_qos_best_effort() -> None:
    """Best-effort string maps to BEST_EFFORT policy."""
    qos = build_qos('best_effort', 5)
    assert qos.reliability == ReliabilityPolicy.BEST_EFFORT
    assert qos.depth == 5


def test_build_qos_rejects_unknown() -> None:
    """Unknown reliability string raises ValueError."""
    with pytest.raises(ValueError):
        build_qos('nonsense', 10)
