# Odom Adapter Documentation

## Входные данные
- **Топик**: `/vehicle/odom_gz`
- **Тип**: `nav_msgs/msg/Odometry`
- **Источник**: `ros_gz_bridge` (из Gazebo)
- **Исходные фреймы**: `header.frame_id = "course_ackermann/odom"`, `child_frame_id = "course_ackermann/base_link"`

## Выходные данные
- **Топик**: `/vehicle/odom`
- **Тип**: `nav_msgs/msg/Odometry`
- **Нормализованные фреймы**: `header.frame_id = "odom"`, `child_frame_id = "base_link"`

## Публикация TF
- Нода `odom_adapter` является **единственным владельцем** динамической связи `odom -> base_link`.
- Она публикует `TransformStamped` в топик `/tf`, используя позицию и ориентацию из сообщения `Odometry`.
- Статические связи (`base_link -> camera_link`, `base_link -> lidar_link`, `base_link -> imu_link`) публикуются нодой `robot_state_publisher` в `/tf_static`.

## Время и QoS
- Нода использует параметр `use_sim_time: true`, поэтому все `stamp` синхронизированы с `/clock`.
- QoS профиль: `RELIABLE`, `KEEP_LAST (10)`.

## Нормализация
Адаптер принимает сырую одометрию от Gazebo с нестандартными именами фреймов (`course_ackermann/odom` и `course_ackermann/base_link`) и нормализует их к стандартным именам ROS (`odom` и `base_link`). Это необходимо для совместимости с другими ROS-нодами и инструментами навигации.
