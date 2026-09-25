### `ros2 pkg prefix turtlesim`
- **Точная команда:** `ros2 pkg prefix turtlesim`
- **Назначение:** Показывает путь, по которому установлен указанный пакет ROS 2 (в данном случае `turtlesim`).
- **Результат:** Вывод `/opt/ros/lyrical`. Это позволило убедиться, что пакет установлен, и найти его исходные файлы.

### `n>&k` (перенаправление файловых дескрипторов)
- **Точная команда:** `2>&1` (в составе `colcon build ... 2>&1 | tee ...`)
- **Назначение:** Направить данные из потока `n` в поток `k`. Пример: `2>&1` — направить ошибки (stderr, дескриптор 2) туда же, куда обычный вывод (stdout, дескриптор 1).
- **Результат:** Позволило объединить stdout и stderr команды `colcon build`, чтобы все сообщения (включая ошибки) попали в общий поток и были сохранены через `tee`.

### `tee`
- **Точная команда:** `colcon build ... 2>&1 | tee evidence/pr02/build-empty.txt`
- **Назначение:** Показать переданный результат на экране и одновременно сохранить его в файл.
- **Результат:** В терминале отображался процесс сборки, а в файле `build-empty.txt` сохранился полный лог. Это позволило проанализировать сборку после её завершения.

## Отличие `>` и `|`
- `>` — перенаправляет вывод левой команды в файл, указанный справа (создаёт или перезаписывает файл).
- `|` — передаёт вывод предыдущей команды на вход следующей команде (конвейер).

## `source` vs запуск новой программы
- `source script.sh` — выполняет скрипт **в текущей оболочке**, изменения переменных окружения сохраняются. Например, `source /opt/ros/lyrical/setup.bash` добавляет команды ROS 2 в текущий терминал.
- `bash script.sh` или `./script.sh` — запускает **новый процесс**, изменения окружения не влияют на родительскую оболочку. Поэтому для настройки ROS 2 используется именно `source`.

## Начальное положение черепашки
```bash
fedosdan2@fedosdan2-G5-MF5:~/Study/ROS2$ ros2 topic echo /turtle1/pose --once
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
---
```

## Конечное положение черепашки
```bash
fedosdan2@fedosdan2-G5-MF5:~/Study/ROS2$ ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist   '{linear: {x: 1.0}, angular: {z: 0.5}}'
publisher: beginning loop
publishing #1: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))

fedosdan2@fedosdan2-G5-MF5:~/Study/ROS2$ ros2 topic echo /turtle1/pose --once
x: 6.509308815002441
y: 5.796990871429443
theta: 0.5040000081062317
linear_velocity: 0.0
angular_velocity: 0.0
---
```

## Ввод неправильного имени
```bash
fedosdan2@fedosdan2-G5-MF5:~/Study/ROS2$ ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist   '{linear: {x: 1.0}, angular: {z: 0.5}}'
publisher: beginning loop
publishing #1: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))

fedosdan2@fedosdan2-G5-MF5:~/Study/ROS2$ ros2 topic pub --rate 1 --wait-matching-subscriptions 0 /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}
'
publisher: beginning loop
publishing #1: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))

publishing #2: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))

publishing #3: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))

publishing #4: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))

publishing #5: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))

publishing #6: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))

publishing #7: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))

```

Можно заметить, что команда не доходит до /turtlesim 

## Получение информации по топикам
```bash
fedosdan2@fedosdan2-G5-MF5:~/Study/ROS2$ ros2 topic info /cmd_vel --verbose
Unknown topic '/cmd_vel'
fedosdan2@fedosdan2-G5-MF5:~/Study/ROS2$

fedosdan2@fedosdan2-G5-MF5:~/Study/ROS2$ ros2 topic info /turtle1/cmd_vel --verbose
Type: geometry_msgs/msg/Twist

Publisher count: 0

Subscription count: 1

Node name: sim
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: SUBSCRIPTION
GID: 01.0f.8e.91.a4.6b.8f.7b.00.00.00.00.00.00.2d.04
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (7)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite
fedosdan2@fedosdan2-G5-MF5:~/Study/ROS2$
```