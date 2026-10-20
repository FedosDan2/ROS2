"""Launch robot_state_publisher for course_description."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command
from launch.substitutions import FindExecutable
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    """Build launch description for robot state publisher."""
    pkg_share = FindPackageShare('course_description')

    xacro_path = PathJoinSubstitution([
        pkg_share,
        'urdf',
        'vehicle.urdf.xacro',
    ])

    robot_description = Command([
        FindExecutable(name='xacro'),
        ' ',
        xacro_path,
    ])

    return LaunchDescription([
        DeclareLaunchArgument(
            'rviz',
            default_value='false',
            description='Open RViz together with state publisher',
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': robot_description,
            }],
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
