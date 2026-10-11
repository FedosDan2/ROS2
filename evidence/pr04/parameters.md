# ПР04 — Параметризуем движение

## Окружение

- ROS 2: **Lyrical** (Python 3.14, `/usr/bin/python3`)
- Workspace: `~/Study/ROS2`
- Пакет: `patrol` (`ament_python`, `rclpy`)
- Нода: `/patrol`
- Тип позы: `turtlesim_msgs/msg/Pose` (проверено через `ros2 topic type /turtle1/pose`)
- Топик команды после remap: `/turtle1/cmd_vel`
- Сообщение команды: `geometry_msgs/msg/Twist`

## Параметры ноды

| Параметр | Default | Допустимый диапазон |
|---|---:|---:|
| `linear_speed` | 0.5 | [0.0, 1.0] |
| `turn_rate` | 0.3 | [-1.0, 1.0] |
| `publish_hz` | 10.0 | [1.0, 30.0] |

Валидация выполняется **до** изменения активного состояния (таймера). При допустимой смене `publish_hz` старый таймер останавливается через `cancel()` и создаётся новый с периодом `1 / publish_hz`; двух одновременных таймеров не остаётся.

Чистые функции `validate_*` и `compute_command` покрыты pytest (см. `tests.txt`): проверяются обычный переход 10→5, ноль, отрицательное значение и NaN.

## Стадия «Собрать»: рабочие параметры

Запуск:

```bash
ros2 run turtlesim turtlesim_node
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

Логи ноды:

```text
[INFO] [<ts>] [patrol]: Patrol started at 10.000 Hz
```

Значения по умолчанию:

```bash
ros2 param get /patrol linear_speed
ros2 param get /patrol turn_rate
ros2 param get /patrol publish_hz
```

```text
Double value is: 0.5
Double value is: 0.3
Double value is: 10.0
```

Измерение частоты при `publish_hz = 10.0`:

```bash
timeout 10 ros2 topic hz /turtle1/cmd_vel --window 100
```

```text
average rate: 10.001
        min: 0.100s max: 0.100s std dev: 0.00022s window: 9
average rate: 9.999
        min: 0.100s max: 0.100s std dev: 0.00019s window: 19
average rate: 10.000
        min: 0.100s max: 0.100s std dev: 0.00021s window: 29
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00023s window: 39
average rate: 10.001
        min: 0.100s max: 0.101s std dev: 0.00022s window: 49
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00021s window: 59
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00020s window: 69
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00020s window: 79
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00020s window: 89
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00020s window: 99
```

Средняя частота ≈ 10 Гц соответствует периоду таймера `1 / 10 = 0.1` с.

Смена частоты 10 → 5:

```bash
ros2 param set /patrol publish_hz 5.0
ros2 param get /patrol publish_hz
```

```text
Set parameter successful
Double value is: 5.0
```

Отклонение недопустимого верхнего значения (валидация включена):

```bash
ros2 param set /patrol publish_hz 300.0
```

```text
Setting parameter failed: publish_hz must be in [1.0, 30.0]
```

Значение при этом не изменилось — активное состояние не тронуто.

## `linear_speed` и `turn_rate`

Допустимые значения принимаются:

```bash
ros2 param set /patrol linear_speed 0.25
ros2 param set /patrol turn_rate -0.5
ros2 param get /patrol linear_speed
ros2 param get /patrol turn_rate
```

```text
Set parameter successful
Set parameter successful
Double value is: 0.25
Double value is: -0.5
```

Недопустимые значения отклоняются, старые сохраняются:

```bash
ros2 param set /patrol linear_speed 2.0
ros2 param set /patrol turn_rate -2.0
ros2 param get /patrol linear_speed
ros2 param get /patrol turn_rate
```

```text
Setting parameter failed: linear_speed must be in [0.0, 1.0]
Setting parameter failed: turn_rate must be in [-1.0, 1.0]
Double value is: 0.25
Double value is: -0.5
```

Это подтверждает требование: проверка входа выполняется до изменения активного состояния.

## NaN на уровне CLI

```bash
ros2 param set /patrol publish_hz nan
```

```text
Setting parameter failed: Wrong parameter type, expected '3' got '4'
```

CLI отклоняет NaN по типу параметра ещё до вызова валидации ноды. Сама проверка неконечных значений (`math.isfinite`) покрыта чистым тестом `test_publish_hz_rejects_nan` в `tests.txt`.

## Стадия «Сломать»: воспроизводимый отказ без валидации

На **временной ветке дефекта** (`pr04-defect`) проверка `publish_hz` была намеренно отключена: в `_on_set_parameters` вместо `validate_publish_hz(number)` подставлялось сырое `number`. После пересборки:

```bash
ros2 param set /patrol publish_hz 0.0
```

Нода приняла ноль и попыталась пересоздать таймер с периодом `1.0 / 0.0`, что привело к падению:

```text
Traceback (most recent call last):
  File ".../install/patrol/lib/patrol/patrol", line 33, in <module>
    sys.exit(load_entry_point('patrol', 'console_scripts', 'patrol')())
  File ".../build/patrol/patrol/patrol.py", line 263, in main
    rclpy.spin(node)
  ...
  File ".../build/patrol/patrol/patrol.py", line 240, in _on_set_parameters
    self._restart_timer(new_publish_hz)
  File ".../build/patrol/patrol/patrol.py", line 185, in _restart_timer
    1.0 / publish_hz,
    ~~~~^~~~~~~~~~~~
ZeroDivisionError: division by zero
[ros2run]: Process exited with failure 1
```

Конкретный отказ: `ZeroDivisionError` в `_restart_timer`, процесс ноды завершён с кодом 1, активное состояние разрушено. Отказ воспроизводим: достаточно повторно отключить валидацию и установить `publish_hz=0.0`.

## Стадия «Доказать»: ноль отклонён, старая частота сохранена

Возвращаем валидацию (основная ветка реализации), пересобираем и запускаем ноду. Сначала фиксируем допустимое рабочее значение 5 Гц, чтобы было видно, что именно оно сохраняется после отклонённого нуля:

```bash
ros2 param set /patrol publish_hz 5.0
ros2 param get /patrol publish_hz
timeout 10 ros2 topic hz /turtle1/cmd_vel --window 100
```

```text
Set parameter successful
Double value is: 5.0
average rate: 5.001
        min: 0.200s max: 0.200s std dev: 0.00031s window: 9
average rate: 4.999
        min: 0.200s max: 0.201s std dev: 0.00028s window: 19
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00027s window: 29
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00026s window: 39
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00025s window: 49
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00025s window: 59
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00025s window: 69
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00025s window: 79
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00025s window: 89
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00025s window: 99

```

Теперь пробуем недопустимый ноль:

```bash
ros2 param set /patrol publish_hz 0.0
```

```text
Setting parameter failed: publish_hz must be in [1.0, 30.0]
```

Проверяем, что старое значение сохранилось и нода не упала:

```bash
ros2 param get /patrol publish_hz
```

```text
Double value is: 5.0
```

Проверяем, что поток команд не изменился (частота осталась 5 Гц, а не стала 0 или не удвоилась из-за двух таймеров):

```bash
timeout 10 ros2 topic hz /turtle1/cmd_vel --window 100
```

```text
Set parameter successful
Double value is: 5.0
average rate: 5.001
        min: 0.200s max: 0.200s std dev: 0.00031s window: 9
average rate: 4.999
        min: 0.200s max: 0.201s std dev: 0.00028s window: 19
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00027s window: 29
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00026s window: 39
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00025s window: 49
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00025s window: 59
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00025s window: 69
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00025s window: 79
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00025s window: 89
average rate: 5.000
        min: 0.200s max: 0.201s std dev: 0.00025s window: 99
```

Допустимое изменение обратно подтверждает, что валидация не ломает рабочий путь:

```bash
ros2 param set /patrol publish_hz 10.0
ros2 param get /patrol publish_hz
timeout 10 ros2 topic hz /turtle1/cmd_vel --window 100
```

```text
Set parameter successful
Double value is: 10.0
average rate: 10.001
        min: 0.100s max: 0.100s std dev: 0.00022s window: 9
average rate: 9.999
        min: 0.100s max: 0.100s std dev: 0.00020s window: 19
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00021s window: 29
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00021s window: 39
average rate: 10.001
        min: 0.100s max: 0.101s std dev: 0.00020s window: 49
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00020s window: 59
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00020s window: 69
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00020s window: 79
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00020s window: 89
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00020s window: 99
```

Вывод: ноль отклонён до изменения таймера; старая частота 5 Гц и активное состояние сохранены; допустимое значение реально меняет поток. Дефект из предыдущей стадии устранён.
