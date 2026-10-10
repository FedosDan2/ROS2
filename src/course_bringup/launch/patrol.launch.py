from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """Build launch description with namespace, remap and record."""
    namespace = LaunchConfiguration('namespace')
    record = LaunchConfiguration('record')
    bag_dir = LaunchConfiguration('bag_dir')
    subscriber_reliability = LaunchConfiguration('subscriber_reliability')

    sensor_topic = ['/', namespace, '/sensor_pose']

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace',
            default_value='robot_a',
            description='Namespace for patrol and pose_relay',
        ),

        DeclareLaunchArgument(
            'record',
            default_value='false',
            description='Start rosbag2 MCAP recorder',
        ),

        DeclareLaunchArgument(
            'bag_dir',
            default_value='evidence/pr05/bag',
            description='Output directory for MCAP bag',
        ),

        DeclareLaunchArgument(
            'subscriber_reliability',
            default_value='reliable',
            description='QoS reliability for pose_relay listener',
        ),

        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim',
            output='screen',
        ),

        Node(
            package='patrol',
            executable='patrol',
            name='patrol',
            namespace=namespace,
            output='screen',
            remappings=[
                ('cmd_vel', '/turtle1/cmd_vel'),
            ],
        ),

        Node(
            package='course_bringup',
            executable='pose_relay',
            name='pose_relay',
            namespace=namespace,
            output='screen',
            parameters=[{
                'subscriber_reliability': subscriber_reliability,
            }],
        ),

        ExecuteProcess(
            cmd=[
                'ros2', 'bag', 'record',
                '-s', 'mcap',
                '-o', bag_dir,
                '--topics', sensor_topic,
            ],
            output='screen',
            condition=IfCondition(record),
        ),
    ])
