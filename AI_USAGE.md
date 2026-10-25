# Использование ИИ

- Использован ИИ: да, Qwen3.7.
- Затронутые файлы: `src/course_simulation/launch/simulation.launch.py`, `src/course_simulation/course_simulation/ackermann_adapter.py`, `src/course_simulation/course_simulation/odom_adapter.py`, `src/course_simulation/test/test_ackermann_adapter.py`, `src/course_simulation/test/test_odom_adapter.py`
- Помощь:
  - разбор архитектуры Gazebo, `ros_gz_bridge` и разницы между bridge (переводчик) и adapter (инженер по безопасности);
  - написание адаптеров `ackermann_adapter` (валидация, clamping, кинематика Аккермана) и `odom_adapter` (нормализация фреймов + публикация TF `odom → base_link`);
  - объяснение `use_sim_time`, `/clock` и флага `--use-sim-time` при записи bag;
