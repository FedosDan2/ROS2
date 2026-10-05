# ПР03 — Первая нода: поза и команда

## Окружение

- ROS 2: **Lyrical** (Python 3.14, `/usr/bin/python3`)
- Workspace: `~/Study/ROS2`
- Пакет: `patrol` (`ament_python`, `rclpy`)
- Тип позы: `turtlesim_msgs/msg/Pose` (проверено через `ros2 topic type /turtle1/pose`)
- Топик позы: `/turtle1/pose`
- Топик команды до remap: относительный `cmd_vel` → разрешается в `/cmd_vel`
- Топик команды после remap: `/turtle1/cmd_vel`
- Сообщение команды: `geometry_msgs/msg/Twist`
- Период таймера: 0.1 с → ожидаемая частота публикации ≈ 10 Гц

## Что делает нода (стадия «Собрать»)

Нода `Patrol` в конструкторе создаёт три объекта и сохраняет их как поля:

1. `self.subscription` — подписка на `/turtle1/pose`, коллбэк `pose_callback` **только** сохраняет последнее сообщение в `self.last_pose`. Никакой тяжёлой работы в коллбэке нет, чтобы не блокировать executor.
2. `self.publisher` — издатель `geometry_msgs/msg/Twist` в относительный топик `cmd_vel`.
3. `self.timer` — таймер с периодом 0.1 с, коллбэк `timer_callback` вызывает чистую функцию `compute_command(self.last_pose)` и публикует результат.

Чистая функция `compute_command()`:

- если поза отсутствует (`None`) → возвращает нулевой `Twist`;
- если поза есть → возвращает `linear.x = 0.5`, `angular.z = 0.3`, прогнанные через `clamp()` в допустимые диапазоны `linear.x ∈ [0, 0.5]`, `angular.z ∈ [-1, 1]`.

Такое разделение нужно, чтобы логику выбора команды можно было тестировать без ROS-графа (что и сделано в `test_patrol.py`).

## Роли элементов ROS 2

### `rclpy.init()`

Инициализирует контекст DDS-коммуникации (участие в графе, discovery, обмен сообщениями). Без вызова `rclpy.init()` нельзя создать ни одну ноду. Вызывается один раз в начале `main()`.

### `Patrol.__init__()` (конструктор ноды)

Регистрирует ноду `patrol` в графе, создаёт подписку, издатель и таймер. Все три объекта сохраняются как поля экземпляра — это требование задания («сохраните подписку как поле объекта»). Если бы подписка не была сохранена, Python мог бы собрать её как мусор, и коллбэк перестал бы вызываться.

### `pose_callback()`

Вызывается executor'ом каждый раз, когда в `/turtle1/pose` приходит новое сообщение. Делает ровно одно: `self.last_pose = msg`. Это правильный паттерн: коллбэки должны быть короткими, иначе они блокируют обработку других событий (таймера, других подписок).

### `timer_callback()`

Вызывается executor'ом каждые 0.1 с. Берёт последнюю сохранённую позу, передаёт её в чистую функцию `compute_command()`, публикует результат. До получения первой позы `self.last_pose is None`, поэтому публикуется нулевой `Twist` — робот «стоит», пока не увидит состояние мира.

### `rclpy.spin(node)`

Запускает цикл executor'а: ждёт наступления событий (таймер, входящее сообщение, сигнал) и вызывает соответствующие коллбэки. Без `spin()` конструктор отработал бы, ноды создались бы, но ни один коллбэк никогда не был бы вызван — топики не публиковались бы, позы не сохранялись бы.

### `Ctrl+C` (KeyboardInterrupt) и штатная остановка

`Ctrl+C` генерирует `KeyboardInterrupt` в главном потоке. В `main()` он перехватывается, и в блоке `finally` выполняется:

1. `node.send_zero()` — явная публикация нулевого `Twist` **до** уничтожения ноды;
2. `node.destroy_node()` — освобождение ресурсов ноды;
3. `rclpy.shutdown()` — закрытие контекста.

Ключевой момент курса: **исчезновение процесса ≠ команда торможения**. Если просто убить процесс (`kill -9`), последнее ненулевое сообщение `Twist` может кратковременно остаться в подписке turtlesim, и черепаха продолжит движение «по инерции» графа. Поэтому мы явно отправляем нулевую команду перед выходом. Метод `send_zero()` обёрнут в `try/except`, потому что при некоторых условиях остановки контекст уже может быть инвалидирован — в этом случае публикация невозможна, и это не должно ронять процесс с traceback.

После остановки `patrol` нужно дождаться остановки `turtlesim` — не считать исчезновение нашего процесса мгновенной командой стоп для всей системы.

## Стадия «Сломать»: разрыв имени топика

Запуск без remap:

```bash
ros2 run turtlesim turtlesim_node        # терминал 1
ros2 run patrol patrol                   # терминал 2 (без -r)
```

### Список топиков

```text
$ ros2 topic list
/cmd_vel
/parameter_events
/rosout
/turtle1/cmd_vel
/turtle1/color_sensor
/turtle1/pose
```

Видны **два разных** топика команды: `/cmd_vel` (наш относительный, разрешённый в корень) и `/turtle1/cmd_vel` (который слушает turtlesim). Они не соединены.

### Наш издатель смотрит в пустоту

```text
$ ros2 topic info /cmd_vel -v
Type: geometry_msgs/msg/Twist

Publisher count: 1

Node name: patrol
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: PUBLISHER
GID: 01.0f.49.e6.4a.c4.04.52.00.00.00.00.00.00.14.03
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (10)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite

Subscription count: 0
```

`Publisher count: 1`, `Subscription count: 0` — patrol публикует команды, но их **никто не читает**.

### turtlesim ждёт, но никто не шлёт

```text
$ ros2 topic info /turtle1/cmd_vel -v
Type: geometry_msgs/msg/Twist

Publisher count: 0

Subscription count: 1

Node name: turtlesim
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: SUBSCRIPTION
GID: 01.0f.49.e6.ee.c3.fb.c3.00.00.00.00.00.00.1c.04
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (7)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite
```

`Publisher count: 0`, `Subscription count: 1` — turtlesim подписан, но **источника нет**.

### Поза при этом доступна

```text
$ ros2 topic echo /turtle1/pose --once
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
---
```

Это важный диагностический факт: подписка на позу работает, данные приходят, `self.last_pose` заполняется, `compute_command()` возвращает ненулевой `Twist`. Значит, отказ **не** в датчике и **не** в логике ноды.

### Наблюдение

Черепаха **не двигается**. Команды уходят в `/cmd_vel`, где нет подписчика; turtlesim слушает `/turtle1/cmd_vel`, куда никто не публикует.

### Анализ причины отказа

Сравниваем QoS обоих endpoint'ов:

- `/cmd_vel` (publisher patrol): RELIABLE / KEEP_LAST(10) / VOLATILE;
- `/turtle1/cmd_vel` (subscriber turtlesim): RELIABLE / KEEP_LAST(7) / VOLATILE.

Профили совместимы (RELIABLE publisher + RELIABLE subscriber, VOLATILE + VOLATILE, глубина history не конфликтует). Значит, причина **не в QoS-несовместимости**, которая была бы частой ловушкой в ROS 2. Причина чисто в **имени топика**: относительный `cmd_vel` разрешается в `/cmd_vel`, а не в `/turtle1/cmd_vel`. Это классический отказ «разрыв графа по имени» — ноды живы, данные есть, но соединения нет.

## Стадия «Доказать»: remap восстанавливает связь

Останавливаем patrol (`Ctrl+C`), перезапускаем с remap:

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

Флаг `-r cmd_vel:=/turtle1/cmd_vel` говорит ROS 2: «всё, что нода называет относительным `cmd_vel`, на самом деле должно быть `/turtle1/cmd_vel`». Логика ноды не меняется — меняется только разрешение имени на уровне графа.

### Связь восстановлена

```text
$ ros2 topic info /turtle1/cmd_vel -v
Type: geometry_msgs/msg/Twist

Publisher count: 1

Node name: patrol
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: PUBLISHER
GID: 01.0f.49.e6.12.c9.09.aa.00.00.00.00.00.00.14.03
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (10)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite

Subscription count: 1

Node name: turtlesim
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: SUBSCRIPTION
GID: 01.0f.49.e6.ee.c3.fb.c3.00.00.00.00.00.00.1c.04
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (7)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite
```

Теперь на `/turtle1/cmd_vel` одновременно `Publisher count: 1` (patrol) и `Subscription count: 1` (turtlesim). Turtle type hash совпадает у обоих endpoint'ов — типы сообщений идентичны. Черепаха начинает двигаться по дуге (`linear.x = 0.5`, `angular.z = 0.3`).

### Измерение реальной частоты за 10 секунд

```text
$ timeout 10 ros2 topic hz /turtle1/cmd_vel --window 100
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00030s window: 9
average rate: 10.001
        min: 0.100s max: 0.101s std dev: 0.00026s window: 19
average rate: 10.001
        min: 0.100s max: 0.101s std dev: 0.00027s window: 29
average rate: 10.001
        min: 0.100s max: 0.101s std dev: 0.00024s window: 39
average rate: 10.001
        min: 0.100s max: 0.101s std dev: 0.00024s window: 49
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00022s window: 59
average rate: 10.001
        min: 0.100s max: 0.101s std dev: 0.00022s window: 69
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00022s window: 79
average rate: 10.000
        min: 0.100s max: 0.101s std dev: 0.00021s window: 89
failed to initialize wait set: the given context is not valid, either rcl_init() was not called or rcl_shutdown() was called., at ./src/rcl/wait.c:110
```

Интерпретация:

- средняя частота стабильно **10.000–10.001 Гц** — ровно соответствует периоду таймера 0.1 с;
- межпакетный интервал `min 0.100s, max 0.101s` — ни одного пропуска или накопления;
- `std dev` падает с 0.00030 до 0.00021 с по мере роста окна — таймер работает детерминированно, дрейфа нет;
- за 10 секунд накоплено ~89–99 сообщений в окне 100 — это ожидаемое число для 10 Гц;
- последняя строка про «context is not valid» — **не ошибка patrol**, а артефакт завершения самого измерителя `ros2 topic hz` по сигналу от `timeout 10`: процесс измерителя закрывает свой rcl-контекст и пытается инициализировать wait set уже после shutdown. Нода patrol в этот момент работает штатно.

### Итог стадии «Доказать»

Remap соединил издатель patrol с подписчиком turtlesim. Частота команды измерена и совпадает с расчётной (10 Гц). Гипотеза «отказ был в имени топика, а не в логике/QoS/позе» подтверждена: до remap — связь 1×0, после remap — связь 1×1, движение появилось, частота стабильна.

## Выводы по работе

1. Нода с подпиской + таймером + издателем собрана и работает; логика выбора команды вынесена в чистую функцию и покрыта тестами (отсутствующая поза → ноль; обычная поза → требуемый ограниченный Twist).
2. Дефект «публикация в относительный `cmd_vel`, не соединённый с `/turtle1/cmd_vel`» воспроизведён: черепаха стоит, `/cmd_vel` имеет 1 publisher и 0 subscribers, `/turtle1/cmd_vel` имеет 0 publishers и 1 subscriber, при этом поза приходит — значит отказ не в сенсоре.
3. Дефект исправлен штатным средством ROS 2 — remap'ом `-r cmd_vel:=/turtle1/cmd_vel`, без изменения кода ноды. Связь восстановлена (1×1), черепаха движется, частота ≈ 10 Гц за 10 секунд.
4. QoS-профили издателя и подписчика оказались совместимы, поэтому несвязность объяснялась именно именем, а не политикой доставки — это различие важно при диагностике отказов графа.
5. Штатная остановка через `Ctrl+C` сопровождается явной публикацией нулевого `Twist` до уничтожения ноды; исчезновение процесса не тождественно команде торможения, что и требовалось показать и объяснить.
