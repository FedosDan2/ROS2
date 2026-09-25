## Topic List
```bash
fedosdan2@fedosdan2-G5-MF5:~/Study/ROS2$ ros2 topic list -t
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
/turtle1/cmd_vel [geometry_msgs/msg/Twist]
/turtle1/color_sensor [turtlesim_msgs/msg/Color]
/turtle1/pose [turtlesim_msgs/msg/Pose]
```
| Топик | Тип | Назначение |
|:--------|:--------:|-------:|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | Топик для передачи команд движения черепахи |
| `/turtle1/color_sensor` | `turtlesim_msgs/msg/Color` | Топик, отвечающий за цвет линии под черепахой |
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | Топик текущей позы черепахи |  
