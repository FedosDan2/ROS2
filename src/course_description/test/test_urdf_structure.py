"""Structural tests for course_description xacro."""

from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import pytest

PKG_DIR = Path(__file__).resolve().parents[1]
XACRO_FILE = PKG_DIR / 'urdf' / 'vehicle.urdf.xacro'

REQUIRED_LINKS = {
    'base_link',
    'camera_link',
    'lidar_link',
    'imu_link',
    'front_left_knuckle',
    'front_right_knuckle',
    'front_left_wheel',
    'front_right_wheel',
    'rear_left_wheel',
    'rear_right_wheel',
}

SENSOR_JOINTS = {
    'camera_joint': ('base_link', 'camera_link'),
    'lidar_joint': ('base_link', 'lidar_link'),
    'imu_joint': ('base_link', 'imu_link'),
}

STEERING_JOINTS = {
    'front_left_steering_joint': (
        'base_link',
        'front_left_knuckle',
    ),
    'front_right_steering_joint': (
        'base_link',
        'front_right_knuckle',
    ),
}

WHEEL_JOINTS = {
    'front_left_wheel_joint': (
        'front_left_knuckle',
        'front_left_wheel',
    ),
    'front_right_wheel_joint': (
        'front_right_knuckle',
        'front_right_wheel',
    ),
    'rear_left_wheel_joint': (
        'base_link',
        'rear_left_wheel',
    ),
    'rear_right_wheel_joint': (
        'base_link',
        'rear_right_wheel',
    ),
}


def expand_xacro() -> str:
    """Expand xacro file to URDF string."""
    if shutil.which('xacro') is None:
        pytest.skip('xacro executable not found')

    result = subprocess.run(
        ['xacro', str(XACRO_FILE)],
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout


def parse_urdf() -> ET.Element:
    """Parse expanded URDF."""
    return ET.fromstring(expand_xacro())


def test_xacro_expands_without_gazebo_plugins() -> None:
    """Expanded URDF must not contain Gazebo-specific blocks."""
    urdf = expand_xacro()

    assert '<plugin' not in urdf
    assert '<sensor' not in urdf
    assert 'gz_frame_id' not in urdf
    assert 'update_rate' not in urdf


def test_required_links_exist() -> None:
    """Required links exist."""
    root = parse_urdf()

    assert root.tag == 'robot'

    links = {
        link.get('name')
        for link in root.findall('link')
    }

    assert REQUIRED_LINKS.issubset(links)


def test_sensor_parents_are_base_link() -> None:
    """Fixed sensors must be children of base_link."""
    root = parse_urdf()

    joints = {
        joint.get('name'): joint
        for joint in root.findall('joint')
    }

    for name, expected in SENSOR_JOINTS.items():
        parent, child = expected

        assert name in joints

        joint = joints[name]

        assert joint.get('type') == 'fixed'
        assert joint.find('parent').get('link') == parent
        assert joint.find('child').get('link') == child


def test_steering_joints_are_revolute() -> None:
    """Steering joints are revolute and parented to base_link."""
    root = parse_urdf()

    joints = {
        joint.get('name'): joint
        for joint in root.findall('joint')
    }

    for name, expected in STEERING_JOINTS.items():
        parent, child = expected

        assert name in joints

        joint = joints[name]

        assert joint.get('type') == 'revolute'
        assert joint.find('parent').get('link') == parent
        assert joint.find('child').get('link') == child

        limit = joint.find('limit')
        assert limit is not None
        assert float(limit.get('lower')) < 0.0
        assert float(limit.get('upper')) > 0.0


def test_wheel_joints_are_continuous() -> None:
    """Wheel joints are continuous and have expected parents."""
    root = parse_urdf()

    joints = {
        joint.get('name'): joint
        for joint in root.findall('joint')
    }

    for name, expected in WHEEL_JOINTS.items():
        parent, child = expected

        assert name in joints

        joint = joints[name]

        assert joint.get('type') == 'continuous'
        assert joint.find('parent').get('link') == parent
        assert joint.find('child').get('link') == child


def test_tree_is_connected_and_acyclic() -> None:
    """All non-root links have one parent and no cycles."""
    root = parse_urdf()

    links = {
        link.get('name')
        for link in root.findall('link')
    }

    parents = {}

    for joint in root.findall('joint'):
        child = joint.find('child').get('link')
        parent = joint.find('parent').get('link')

        assert child in links
        assert parent in links
        assert child not in parents

        parents[child] = parent

    roots = links - set(parents)

    assert roots == {'base_link'}

    for link in links:
        seen = set()
        current = link

        while current in parents:
            assert current not in seen
            seen.add(current)
            current = parents[current]

        assert current == 'base_link'


def test_inertias_are_positive() -> None:
    """Diagonal inertias are positive and off-diagonal zero."""
    root = parse_urdf()

    for link in root.findall('link'):
        link_name = link.get('name')
        inertial = link.find('inertial')

        if inertial is None:
            continue

        mass_elem = inertial.find('mass')

        if mass_elem is None:
            continue

        mass_val = mass_elem.get('value')

        if mass_val is None:
            continue

        mass = float(mass_val)
        assert mass > 0.0

        inertia = inertial.find('inertia')

        if inertia is None:
            raise AssertionError(
                f'Link {link_name} has mass but no inertia tag'
            )

        for axis in ('ixx', 'iyy', 'izz'):
            val_str = inertia.get(axis)

            if val_str is None:
                raise AssertionError(
                    f'Link {link_name} missing inertia attribute {axis}'
                )

            assert float(val_str) > 0.0

        for axis in ('ixy', 'ixz', 'iyz'):
            val_str = inertia.get(axis)

            if val_str is not None:
                assert float(val_str) == 0.0
