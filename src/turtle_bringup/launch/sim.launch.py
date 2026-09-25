from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # 1. Объявляем аргумент launch-файла
    teleop_arg = DeclareLaunchArgument(
        'teleop',
        default_value='0',
        description='Запустить turtle_teleop_key: 1 — да, 0 — нет',
    )

    # 2. Объект, который "читает" значение аргумента
    teleop_enabled = LaunchConfiguration('teleop')

    # 3. Основной узел — всегда
    turtlesim_node = Node(
        package='turtlesim',
        executable='turtlesim_node',
        name='sim',
        output='screen',
    )

    # 4. Teleop — только если teleop == 1
    teleop_node = Node(
        package='turtlesim',
        executable='turtle_teleop_key',
        name='teleop',
        output='screen',
        condition=IfCondition(teleop_enabled),
        prefix='xterm -e'  

    )

    return LaunchDescription([
        teleop_arg,
        turtlesim_node,
        teleop_node,
    ])