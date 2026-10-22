# Открытые контракты ROS 2

## Границы топиков

| Топик | Тип | Издатель | Подписчик | Правило |
|---|---|---|---|---|
| `/perception/scene` | `robotics_course_interfaces/msg/SceneDescription` | адаптер восприятия | планировщик/контроллер | только типизированное наблюдение v1 |
| `/drive/raw` | `ackermann_msgs/msg/AckermannDriveStamped` | контроллер/политика | supervisor безопасности | не соединяется с Gazebo напрямую |
| `/drive/safe` | `ackermann_msgs/msg/AckermannDriveStamped` | supervisor безопасности | адаптер привода | единственный источник команды приводу |
| `/safety/status` | `robotics_course_interfaces/msg/SafetyStatus` | supervisor безопасности | evaluator/наблюдатель | последнее состояние сохраняется |
| `/scenario/run` | `robotics_course_interfaces/srv/RunScenario` | evaluator | исполнитель сценария | ID манифеста + seed |

Сенсорные топики находятся в `/vehicle/`: `/vehicle/camera/image_raw`,
`/vehicle/scan`, `/vehicle/imu`, `/vehicle/odom`. Их `header.stamp` использует
время симуляции, а frame ID входят в одно дерево tf с корнем `base_link`.

## QoS

- камера, лидар и IMU: профиль sensor data, best effort, keep last;
- одометрия и команды движения: reliable, keep last;
- состояние безопасности: reliable + transient local;
- сервис сценария: reliable.

Каждый адаптер предоставляет параметры имён топиков, но значения выше входят в
контракт квалификации. Пространство имён можно дополнить командным префиксом;
жёстко заданные глобальные псевдонимы вне контракта не допускаются.

## Нормализация одометрии симулятора

Gazebo публикует исходную одометрию модели с
`header.frame_id=course_ackermann/odom` и
`child_frame_id=course_ackermann/base_link`. В ПР07 исходный
`/vehicle/odom` переназначается в `/vehicle/odom_gz` на bridge, до записи. Единственный адаптер
снимает ровно префикс `course_ackermann/`, сохраняет stamp, pose, twist и обе
covariance и публикует нормализованный `/vehicle/odom` с frames
`odom→base_link`. Он же является единственным владельцем совпадающего
динамического преобразования в `/tf`; сообщения с другим префиксом или
нечисловыми значениями отклоняются. Запись ПР07 уже содержит нормализованную
одометрию и tf; при replay ПР08 этот адаптер повторно не запускается.

## Преобразование Ackermann → Gazebo

Адаптер привода преобразует `AckermannDriveStamped` из `/drive/safe` в
`geometry_msgs/msg/Twist` на `/vehicle/gz_cmd_vel`. Затем `ros_gz_bridge`
переносит этот тип в топик Gazebo-плагина Ackermann. Явная граница не создаёт
ложного впечатления, будто универсальный bridge напрямую поддерживает ROS-
сообщение Ackermann.

Для модели курса адаптер ограничивает конечные числовые значения:
`v = clamp(drive.speed, 0.0, 1.2)` и
`delta = clamp(drive.steering_angle, -0.45, 0.45)`, после чего публикует
`linear.x = v` и `angular.z = v * tan(delta) / 0.8`. Система Gazebo
`AckermannSteering` трактует `angular.z` как угловую скорость корпуса и сама
вычисляет углы рулевых сочленений; `0,8 м` — колёсная база модели. Нечисловой
вход или header старше `0,25 с` даёт нулевой `Twist` и диагностическую причину;
последняя команда после такого отказа не повторяется.

## Heartbeat и восстановление безопасности

Supervisor получает `std_msgs/msg/Empty` в `/safety/heartbeat` с QoS reliable,
keep last. Разрыв дольше `0,25 с` считается отказом. Защёлкнутый `non_finite`
сбрасывается через `/safety/clear_fault` типа `std_srvs/srv/Trigger`; сервис
успешен только после трёх последовательных полных здоровых циклов. В каждом
цикле свежи scene и heartbeat, команда конечна и рядом нет препятствия.
`/drive/raw` и `/drive/safe` используют
`ackermann_msgs/msg/AckermannDriveStamped` с QoS reliable, keep last.

## Версионирование

Несовместимое изменение полей требует новой версии сообщения и миграции топика.
Добавление необязательного наблюдения совместимо только тогда, когда
соответствующее поле `has_*` по умолчанию равно `false`.
