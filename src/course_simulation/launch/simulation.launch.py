"""Launch file for PR07: Gazebo simulation with ros_gz_bridge."""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, SetEnvironmentVariable
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    # Аргументы launch
    world_arg = LaunchConfiguration('world')
    bridge_config_arg = LaunchConfiguration('bridge_config')

    # Пути к файлам пакета course_simulation
    pkg_share = FindPackageShare('course_simulation')
    default_world = PathJoinSubstitution([pkg_share, 'worlds', 'mcity-minimal.sdf'])
    default_bridge_config = PathJoinSubstitution([pkg_share, 'config', 'bridge.yaml'])
    models_path = PathJoinSubstitution([pkg_share, 'models'])

    # Путь к Xacro модели из ПР06
    course_desc_share = FindPackageShare('course_description')
    xacro_file = PathJoinSubstitution([course_desc_share, 'urdf', 'vehicle.urdf.xacro'])
    robot_description = Command([FindExecutable(name='xacro'), ' ', xacro_file])

    # Формируем GZ_SIM_RESOURCE_PATH: добавляем наш models к существующему пути (если он есть)
    current_gz_path = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    if current_gz_path:
        gz_resource_path = [models_path, ':', current_gz_path]
    else:
        gz_resource_path = models_path

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=default_world,
            description='Path to the SDF world file',
        ),
        DeclareLaunchArgument(
            'bridge_config',
            default_value=default_bridge_config,
            description='Path to the bridge YAML configuration',
        ),

        # 1. Исправление: корректная установка переменной окружения для Gazebo
        SetEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=gz_resource_path,
        ),

        # 2. Запуск Gazebo сервера (headless)
        ExecuteProcess(
            cmd=['gz', 'sim', '-s', '-r', '--headless-rendering', world_arg],
            output='screen',
        ),

        # 3. Исправление: корректная передача параметра config_file в ros_gz_bridge
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            output='screen',
            parameters=[{
                'config_file': bridge_config_arg,
                'use_sim_time': True,
            }],
        ),

        # 4. Запуск robot_state_publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'robot_description': robot_description,
            }],
        ),
        
        # 5. Запуск адаптера одометрии
        Node(
            package='course_simulation',
            executable='odom_adapter',
            name='odom_adapter',
            output='screen',
            parameters=[{'use_sim_time': True}],
        ),
    ])
