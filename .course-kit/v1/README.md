# Комплект практикума v1

Комплект содержит общие инструменты и входные файлы уже открытых практик. Он
накопительный: `VERSION` имеет вид `v1-wNN`, а следующая недельная ревизия
добавляет новый манифест и нужные ему входы, не меняя путь `.course-kit/v1`.

## Состав

- `tools/check_practice.py` — проверка структуры evidence и обязательных файлов;
- `tools/workstation_report.sh` — отчёт об ОС, ROS 2 и графическом адаптере;
- `tools/validate_localization.py` — с недели 8 проверка результата ПР08;
- `tools/evaluate_perception.py` — с недели 9 evaluator фиксированного набора ПР09;
- `tools/validate_qualification.py` — с недели 14 проверка результата квалификации;
- `practices/manifests/` — машиночитаемые требования уже открытых ПР;
- `practices/templates/` — шаблоны `report.json` и `AI_USAGE.md`;
- `contracts/` и `interfaces/` — интерфейсы проектной системы;
- `fixtures/`, `scenarios/`, `models/` и `worlds/` — входные данные;
- `vla_actions/` — с недели 13 синтетические входы исполнителя действий;
- `policy_benchmark/` — доступный с недели 12 локальный oracle ПР12;
- `MANIFEST.sha256` — контрольная сумма каждого файла ревизии.

## Использование

Распакуйте архив в каталог `.course-kit/` рядом со своим workspace и добавьте
`.course-kit/` в `.gitignore`. Значение `VERSION` и SHA-256 архива укажите в
evidence текущей работы.

Шаблоны копируются в репозиторий решения так:

```bash
mkdir -p evidence/prNN
cp .course-kit/v1/practices/templates/report.json evidence/prNN/report.json
cp .course-kit/v1/practices/templates/AI_USAGE.md AI_USAGE.md  # если ИИ использовался
```

В ПР01 достаточно CLI-опыта и checker. В ПР02 собирается `turtle_bringup`
с launch-файлом готовой ноды; команды сборки и проверки приведены в ПР02.
С ПР03 из корня репозитория запускайте сборку и функциональные тесты:

```bash
colcon build --symlink-install
colcon test --event-handlers console_direct+
colcon test-result --verbose
python3 .course-kit/v1/tools/check_practice.py PR03 --submission .
```

Замените `PR03` на номер текущей работы. В скопированном `report.json` замените
все значения `replace-with-*`, перенесите трудоёмкость из условия и добавьте
claims из манифеста текущей ПР. В поле `commit` укажите полный SHA готовой
реализации, затем зафиксируйте evidence отдельным commit. Checker
проверяет, что после указанного SHA менялись только файлы текущего evidence и
`AI_USAGE.md`; поведение ROS-системы подтверждают тесты пакетов и команды из
условия.
