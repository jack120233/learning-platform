#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/project_code/backend"
FRONTEND_DIR="$ROOT_DIR/UI"
LOG_DIR="$ROOT_DIR/logs/dev"
MYSQL_BIN="/opt/homebrew/opt/mysql@8.4/bin"
REDIS_BIN="/opt/homebrew/opt/redis/bin"
MYSQL_DATA_DIR="/opt/homebrew/var/mysql"
REDIS_CONF="/opt/homebrew/etc/redis.conf"
PYTHON_BIN="$ROOT_DIR/project_code/.venv/bin/python"

mkdir -p "$LOG_DIR"

port_open() {
  lsof -iTCP:"$1" -sTCP:LISTEN -n -P >/dev/null 2>&1
}

show_port() {
  local port="$1"
  local name="$2"
  if port_open "$port"; then
    printf "%-10s running  http://127.0.0.1:%s\n" "$name" "$port"
    lsof -iTCP:"$port" -sTCP:LISTEN -n -P | tail -n +2
  else
    printf "%-10s stopped  port %s\n" "$name" "$port"
  fi
}

wait_for_port() {
  local port="$1"
  local name="$2"
  for _ in {1..60}; do
    if port_open "$port"; then
      echo "$name 已启动。"
      return 0
    fi
    sleep 1
  done
  echo "$name 启动超时，请查看 $LOG_DIR 日志。" >&2
  return 1
}

require_file() {
  if [[ ! -e "$1" ]]; then
    echo "缺少依赖: $1" >&2
    exit 1
  fi
}

status() {
  echo "服务状态："
  show_port 3306 MySQL
  show_port 6379 Redis
  show_port 8000 Backend
  show_port 3000 Frontend
}

if [[ "${1:-}" == "--status" ]]; then
  status
  exit 0
fi

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "用法: ./start-dev-macos.sh [--status]"
  echo "默认启动 MySQL、Redis、FastAPI 后端和 Vite 前端；按 Ctrl+C 停止本脚本启动的服务。"
  exit 0
fi

require_file "$MYSQL_BIN/mysqld_safe"
require_file "$MYSQL_BIN/mysql"
require_file "$MYSQL_BIN/mysqladmin"
require_file "$REDIS_BIN/redis-server"
require_file "$REDIS_BIN/redis-cli"
require_file "$PYTHON_BIN"
require_file "$FRONTEND_DIR/package.json"
require_file "$BACKEND_DIR/.env"

STARTED_MYSQL=0
STARTED_REDIS=0
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo
  echo "正在停止本脚本启动的服务..."
  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  if [[ "$STARTED_REDIS" == "1" ]]; then
    "$REDIS_BIN/redis-cli" -n 0 shutdown nosave >/dev/null 2>&1 || true
  fi
  if [[ "$STARTED_MYSQL" == "1" ]]; then
    "$MYSQL_BIN/mysqladmin" -u root shutdown >/dev/null 2>&1 || true
  fi
  echo "已停止本脚本启动的服务；原本已在运行的服务不会被停止。"
}
trap cleanup INT TERM EXIT

if grep -q '^DATABASE_URL=mysql+aiomysql://' "$BACKEND_DIR/.env"; then
  echo "后端 .env 当前使用 MySQL。"
else
  echo "警告：后端 .env 可能未使用 MySQL，请检查 $BACKEND_DIR/.env" >&2
fi

if port_open 3306; then
  echo "MySQL 已在 3306 运行，复用现有服务。"
else
  echo "启动 MySQL 8.4..."
  "$MYSQL_BIN/mysqld_safe" --datadir="$MYSQL_DATA_DIR" >"$LOG_DIR/mysql.out.log" 2>"$LOG_DIR/mysql.err.log" &
  STARTED_MYSQL=1
  wait_for_port 3306 MySQL
fi

"$MYSQL_BIN/mysql" -u root -e "CREATE DATABASE IF NOT EXISTS learning_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

if port_open 6379; then
  echo "Redis 已在 6379 运行，复用现有服务。"
else
  echo "启动 Redis..."
  "$REDIS_BIN/redis-server" "$REDIS_CONF" >"$LOG_DIR/redis.out.log" 2>"$LOG_DIR/redis.err.log" &
  STARTED_REDIS=1
  wait_for_port 6379 Redis
fi

if port_open 8000; then
  echo "后端已在 8000 运行，复用现有服务。"
else
  echo "启动 FastAPI 后端..."
  (
    cd "$BACKEND_DIR"
    "$PYTHON_BIN" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
  ) >"$LOG_DIR/backend.out.log" 2>"$LOG_DIR/backend.err.log" &
  BACKEND_PID=$!
  wait_for_port 8000 Backend
fi

if port_open 3000; then
  echo "前端已在 3000 运行，复用现有服务。"
else
  echo "启动 Vite 前端..."
  npm --prefix "$FRONTEND_DIR" run dev -- --host 127.0.0.1 >"$LOG_DIR/frontend.out.log" 2>"$LOG_DIR/frontend.err.log" &
  FRONTEND_PID=$!
  wait_for_port 3000 Frontend
fi

echo
echo "开发环境已就绪："
echo "  前端: http://127.0.0.1:3000/login"
echo "  后端: http://127.0.0.1:8000"
echo "  API 文档: http://127.0.0.1:8000/docs"
echo "  后端健康检查: http://127.0.0.1:8000/api/v1/health"
echo "  日志目录: $LOG_DIR"
echo
echo "按 Ctrl+C 停止本脚本启动的服务。"

while true; do
  sleep 3600
done
