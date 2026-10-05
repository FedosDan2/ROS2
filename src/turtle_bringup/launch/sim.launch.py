"""Launch file for turtle_bringup."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Generate launch description with optional teleop."""
    return LaunchDescription([
        DeclareLaunchArgument(
            'teleop',
            default_value='0',
            description='Запустить turtle_teleop_key: 1 — да, 0 — нет',
        ),

        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='sim',
            output='screen',
        ),

        Node(
            package='turtlesim',
            executable='turtle_teleop_key',
            name='teleop',
            output='screen',
            condition=IfCondition(LaunchConfiguration('teleop')),
            prefix='xterm -e',
        ),
    ])
