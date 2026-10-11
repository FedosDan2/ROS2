
# Шпаргалка для сдачи ПР05 (коротко)

Всё из корня `~/Study/ROS2`, conda выключена.

## 0. Окружение и сборка

```bash
conda deactivate 2>/dev/null || true
source /opt/ros/lyrical/setup.bash
colcon build --symlink-install --packages-select patrol course_bringup
source install/setup.bash
```

## 1. Тесты

```bash
mkdir -p evidence/pr05
python3 -m pytest src/patrol/test src/course_bringup/test -v | tee evidence/pr05/tests.txt
```

Глазами: все `test_patrol` и `test_qos` PASSED, линтеры PASSED, `test_copyright` может быть SKIPPED.

## 2. Сломать (живой поток, reliable → отказ)

```bash
# терминал 1
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=reliable record:=false
```

```bash
# терминал 2, подождать 2-3 с
{
  echo '=== Живой поток: reliable echo (ожидаем отказ) ==='
  timeout 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability reliable --once 2>&1
  echo '=== ros2 topic list ==='
  ros2 topic list
  echo '=== ros2 topic info /robot_a/sensor_pose -v ==='
  ros2 topic info /robot_a/sensor_pose -v
} > evidence/pr05/qos-before.txt
```

Ctrl+C в терминале 1. Глазами в `qos-before.txt`: есть `incompatible QoS` + `Last incompatible policy: RELIABILITY`, есть `/robot_a/sensor_pose` в list, в info publisher `BEST_EFFORT` / subscriber `RELIABLE`, **нет** тела сообщения `x:`.

## 3. Доказать (живой best_effort + запись MCAP)

```bash
# терминал 1 — держать 10-15 с, затем Ctrl+C
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=best_effort \
  record:=true bag_dir:=evidence/pr05/bag
```

```bash
# терминал 2 — НАЧАЛО файла (>)
{
  echo '=== Живой поток: best_effort echo (ожидаем доставку) ==='
  timeout 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability best_effort --once 2>&1
  echo '=== ros2 topic info /robot_a/sensor_pose -v ==='
  ros2 topic info /robot_a/sensor_pose -v
} > evidence/pr05/qos-after.txt
```

Глазами: пришло сообщение `x:/y:/theta:`, в info оба `BEST_EFFORT`. Проверь каталог:

```bash
ls -la evidence/pr05/bag/
```

Должны быть `bag_0.mcap` и `metadata.yaml`.

## 4. Replay (живой launch остановлен! один издатель — playback)

```bash
# терминал A
ros2 bag play evidence/pr05/bag \
  --qos-profile-overrides-path config/qos-overrides.yaml
```

```bash
# терминал B, пока идёт replay — ДОПИСЬ (>>)
{
  echo '=== Replay: reliable subscriber (ожидаем отказ) ==='
  timeout 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability reliable --once 2>&1
  echo '=== Replay: best_effort subscriber (ожидаем доставку) ==='
  timeout 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability best_effort --once 2>&1
} >> evidence/pr05/qos-after.txt
```

Глазами: reliable → WARN incompatible QoS; best_effort → сообщение. Если bag короткий и replay закончился — перезапусти A и повтори B.

```bash
# терминал A — остановить replay Ctrl+C
# терминал B — bag info (ДОПИСЬ >>) + metadata
ros2 bag info evidence/pr05/bag >> evidence/pr05/qos-after.txt
cp evidence/pr05/bag/metadata.yaml evidence/pr05/bag-metadata.yaml
```

Глазами в конце `qos-after.txt`: ровно **одна** строка `Topic information: Topic: /robot_a/sensor_pose`.

## 5. Быстрая самопроверка файлов

```bash
grep -q 'incompatible QoS' evidence/pr05/qos-before.txt && echo 'before: дефект есть'
grep -q '^x:' evidence/pr05/qos-before.txt && echo 'before: ОШИБКА — пришло сообщение'
grep -q 'incompatible QoS' evidence/pr05/qos-after.txt && echo 'after: replay-отказ есть'
grep -q '^x:' evidence/pr05/qos-after.txt && echo 'after: доставка есть'
grep -c 'Topic information' evidence/pr05/qos-after.txt   # ожидаем 1
```

## 6. Два коммита + report.json

```bash
# коммит 1 — реализация
git add src/course_bringup config/qos-overrides.yaml
git commit -m "PR05: course_bringup with pose_relay, launch, namespace, remap, record and qos overrides"
IMPL_SHA=$(git rev-parse HEAD)

# report.json (commit = SHA реализации)
RECORDED_AT_UTC=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
cat > evidence/pr05/report.json <<JSONEOF
{
  "commit": "$IMPL_SHA",
  "recorded_at_utc": "$RECORDED_AT_UTC",
  "ai_used": true,
  "public_tests_passed": true,
  "defect_reproduced": true,
  "defect_fixed": true,
  "replay_verified": true
}
JSONEOF
python3 -m json.tool evidence/pr05/report.json

# коммит 2 — evidence
git add evidence/pr05 AI_USAGE.md
git commit -m "PR05: add qos evidence, bag metadata, tests output and report"
REPORT_SHA=$(git rev-parse HEAD)
```

В `AI_USAGE.md` допиши секцию PR05 (модель, характер помощи, способ проверки), старые записи не трогай.

## 7. Checker

```bash
python3 .course-kit/v1/tools/check_practice.py PR05 --submission .
```

При сдаче указываешь `REPORT_SHA` + ссылку на CI.

---
