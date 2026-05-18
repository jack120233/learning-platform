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

get_pid_on_port() {
  lsof -iTCP:"$1" -sTCP:LISTEN -n -P -t 2>/dev/null | head -1 || true
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

kill_port_process() {
  local port="${1:-}"
  local service_name="${2:-服务}"
  local pid

  [[ -z "$port" ]] && return 0

  pid=$(get_pid_on_port "$port")
  [[ -z "$pid" ]] && return 0

  if kill "$pid" 2>/dev/null; then
    echo "  已关闭 ${service_name}（PID: ${pid}, port: ${port}）"
    for _ in {1..5}; do
      port_open "$port" || return 0
      sleep 1
    done
    echo "  警告: ${service_name} 端口 ${port} 仍未释放" >&2
  else
    echo "  关闭 ${service_name} 失败（PID: ${pid}）" >&2
    return 1
  fi
}

stop_all_services() {
  echo "正在关闭当前项目相关服务..."
  kill_port_process 3000 "前端" || true
  kill_port_process 8000 "后端" || true

  if port_open 6379; then
    "$REDIS_BIN/redis-cli" -n 0 shutdown nosave >/dev/null 2>&1 || kill_port_process 6379 "Redis" || true
    if port_open 6379; then
      echo "  警告: Redis 端口 6379 仍未释放" >&2
    else
      echo "  已关闭 Redis（port: 6379）"
    fi
  fi

  if port_open 3306; then
    "$MYSQL_BIN/mysqladmin" -u root shutdown >/dev/null 2>&1 || kill_port_process 3306 "MySQL" || true
    if port_open 3306; then
      echo "  警告: MySQL 端口 3306 仍未释放" >&2
    else
      echo "  已关闭 MySQL（port: 3306）"
    fi
  fi
}

status() {
  echo "服务状态："
  show_port 3306 MySQL
  show_port 6379 Redis
  show_port 8000 Backend
  show_port 3000 Frontend
}

prompt_start_action() {
  local mysql_pid redis_pid be_pid fe_pid choice=""

  mysql_pid=$(get_pid_on_port 3306)
  redis_pid=$(get_pid_on_port 6379)
  be_pid=$(get_pid_on_port 8000)
  fe_pid=$(get_pid_on_port 3000)

  echo ""
  echo "当前服务状态："
  [[ -n "$mysql_pid" ]] && echo "  MySQL  (PID: $mysql_pid, port: 3306)" || echo "  MySQL  stopped  port 3306"
  [[ -n "$redis_pid" ]] && echo "  Redis  (PID: $redis_pid, port: 6379)" || echo "  Redis  stopped  port 6379"
  [[ -n "$be_pid" ]] && echo "  后端   (PID: $be_pid, port: 8000)" || echo "  后端   stopped  port 8000"
  [[ -n "$fe_pid" ]] && echo "  前端   (PID: $fe_pid, port: 3000)" || echo "  前端   stopped  port 3000"
  echo ""
  echo "请选择操作："
  echo "  1. 关闭全部并重新启动（默认）"
  echo "  2. 直接启动，已运行服务复用"
  echo "  3. 关闭全部并退出"
  printf "请输入 [1/2/3]："

  read -r choice || true
  choice="${choice:-1}"

  case "$choice" in
    1)
      echo ""
      stop_all_services
      echo "服务已关闭，准备重新启动..."
      ;;
    2)
      echo ""
      echo "保留已运行服务，继续启动缺失服务..."
      ;;
    3)
      echo ""
      stop_all_services
      echo "已退出。"
      exit 0
      ;;
    *)
      echo ""
      echo "输入无效，默认执行关闭全部并重新启动..."
      stop_all_services
      echo "服务已关闭，准备重新启动..."
      ;;
  esac
}

cleanup() {
  echo
  stop_all_services
  echo "已关闭当前项目相关服务。"
}

if [[ "${1:-}" == "--status" ]]; then
  status
  exit 0
fi

if [[ "${1:-}" == "--stop" ]]; then
  stop_all_services
  exit 0
fi

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "用法: ./start-dev-macos.sh [--status|--stop]"
  echo "默认固定显示操作菜单；--stop 关闭当前项目的前端、后端、Redis、MySQL。"
  echo "脚本运行期间按 Ctrl+C 或关闭窗口，会关闭当前项目相关服务。"
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

echo "依赖检查通过。"
prompt_start_action
trap 'cleanup; exit 0' INT TERM HUP
trap cleanup EXIT

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
  wait_for_port 3306 MySQL
fi

"$MYSQL_BIN/mysql" -u root -e "CREATE DATABASE IF NOT EXISTS learning_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

if port_open 6379; then
  echo "Redis 已在 6379 运行，复用现有服务。"
else
  echo "启动 Redis..."
  "$REDIS_BIN/redis-server" "$REDIS_CONF" >"$LOG_DIR/redis.out.log" 2>"$LOG_DIR/redis.err.log" &
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
  wait_for_port 8000 Backend
fi

if port_open 3000; then
  echo "前端已在 3000 运行，复用现有服务。"
else
  echo "启动 Vite 前端..."
  npm --prefix "$FRONTEND_DIR" run dev -- --host 127.0.0.1 >"$LOG_DIR/frontend.out.log" 2>"$LOG_DIR/frontend.err.log" &
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
echo "按 Ctrl+C 或关闭当前窗口，会关闭当前项目相关服务。"

while true; do
  sleep 3600
done
