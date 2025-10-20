#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI 未找到，请先安装 Docker Desktop 或 Docker Engine。" >&2
  exit 1
fi

BUILD=false
FOLLOW_LOGS=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build)
      BUILD=true
      shift
      ;;
    --logs)
      FOLLOW_LOGS=true
      shift
      ;;
    *)
      echo "未知参数: $1" >&2
      echo "用法: $0 [--build] [--logs]" >&2
      exit 1
      ;;
  esac
done

if [[ "${BUILD}" == "true" ]]; then
  echo ">> docker compose build --pull"
  docker compose build --pull
fi

echo ">> docker compose up -d"
docker compose up -d

if [[ "${FOLLOW_LOGS}" == "true" ]]; then
  echo
  echo "服务已启动，正在跟随日志输出 (Ctrl+C 退出日志)"
  docker compose logs -f
else
  cat <<EOF

⭐ 服务已启动
   API:        http://localhost:8000/api/v1/docs
   前端页面:  http://localhost:8000/app

可使用 --logs 参数实时查看日志。例如:
  $(basename "$0") --logs
EOF
fi
