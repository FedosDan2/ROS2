#!/usr/bin/env bash

set -uo pipefail

section() {
  printf '\n== %s ==\n' "$1"
}

version_or_missing() {
  local command_name="$1"
  shift
  if command -v "$command_name" >/dev/null 2>&1; then
    "$@" 2>&1 | head -n 3
  else
    printf '[не найдено] %s\n' "$command_name"
  fi
}

section 'Система'
if [[ -r /etc/os-release ]]; then
  grep -E '^(PRETTY_NAME|VERSION_CODENAME)=' /etc/os-release
fi
printf 'архитектура=%s\n' "$(uname -m)"
printf 'ядро=%s\n' "$(uname -r)"
printf 'назначенная оболочка=%s\n' "${SHELL:-<не задано>}"
printf 'текущая оболочка=%s\n' "$(ps -p $$ -o comm= | xargs)"

section 'Инструменты'
version_or_missing bash bash --version
version_or_missing git git --version
version_or_missing fish fish --version
version_or_missing uv uv --version
version_or_missing code code --version
version_or_missing docker docker --version

section 'ROS 2'
printf 'ROS_DISTRO=%s\n' "${ROS_DISTRO:-<не подключено>}"
printf 'ROS_DOMAIN_ID=%s\n' "${ROS_DOMAIN_ID:-<не задано>}"
if command -v ros2 >/dev/null 2>&1; then
  printf 'ros2=%s\n' "$(command -v ros2)"
  ros2 pkg prefix turtlesim 2>&1 || true
else
  printf '[не найдено] ros2; проверьте source /opt/ros/<distro>/setup.bash\n'
fi

section 'Графические адаптеры и драйверы'
if command -v lspci >/dev/null 2>&1; then
  lspci -nnk | grep -EA3 'VGA|3D|Display' || true
else
  printf '[не найдено] lspci; установите pciutils\n'
fi

section 'OpenGL renderer'
if command -v glxinfo >/dev/null 2>&1; then
  glxinfo -B 2>&1 \
    | grep -E 'direct rendering|OpenGL vendor|OpenGL renderer|OpenGL version' \
    || true
else
  printf '[не найдено] glxinfo; установите mesa-utils\n'
fi

section 'Vulkan'
if command -v vulkaninfo >/dev/null 2>&1; then
  vulkaninfo --summary 2>&1 | sed -n '1,45p'
else
  printf '[не найдено] vulkaninfo; установите vulkan-tools\n'
fi

section 'NVIDIA'
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>&1 || true
else
  printf '[не найдено] nvidia-smi; это нормально для Intel/AMD-only системы\n'
fi

printf '\nОтчёт завершён. Перед публикацией просмотрите его вручную.\n'
