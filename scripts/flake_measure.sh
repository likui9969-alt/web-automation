#!/usr/bin/env bash
# flake_measure.sh — 公网 flake 度量（M9 Review P2-2：度量机制跨平台）
#
# 为什么补 bash 版（与 scripts/flake_measure.ps1 等价）：
#   ps1 是 PowerShell，只在 Windows 生效；换环境/换人（或想接进 CI）就断掉，
#   而"度量机制化"的设计初衷恰是"换人换时段都可复现"。bash 版在 Linux/macOS/
#   CI runner（ubuntu）可跑，与 ps1 同一套输出格式，flake 记录口径一致。
#
# 用法：
#   bash scripts/flake_measure.sh -r 3 -m ui
#   bash scripts/flake_measure.sh                  # 默认 Runs=3, Marker=ui
# 输出：逐次结果（PASS/FAIL + 耗时）+ goto 重试计数（若触发）+ 汇总成功率。
# 记录方式：把输出贴到 MODULE_FEEDBACK「flake 记录」节（固定模板）。
#
# 注意：优先用项目 venv 解释器（M6 教训：系统 python 可能是共享 venv，浏览器版本会错位）；
#       Windows 上跑请用 ps1，本脚本面向 Linux/macOS/CI。

set -u  # 未定义变量即报错（不 set -e：逐次运行失败也要继续，度量失败率是目的）

RUNS=3
MARKER="ui"
while getopts "r:m:" opt; do
  case "$opt" in
    r) RUNS="$OPTARG" ;;
    m) MARKER="$OPTARG" ;;
    *) echo "用法: $0 [-r RUNS] [-m MARKER]"; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  # 无 venv 时退回系统 python（记录提示，不硬失败——Linux 下 venv 路径可能与文档略不同）
  PY="python3"
  echo "> 未找到项目 venv ($PY)，改用系统 python3（若浏览器版本错位请先创建 .venv）" >&2
fi

echo "===== flake measure: marker=$MARKER runs=$RUNS $(date '+%Y-%m-%d %H:%M') ====="
echo "(target = public Demo; set ORANGEHRM_* env vars for local)"

PASS=0
for i in $(seq 1 "$RUNS"); do
  OUT="$("$PY" -m pytest -m "$MARKER" 2>&1)"
  CODE=$?
  SUMMARY="$(echo "$OUT" | grep -E "passed|failed|error|skipped" | tail -n 1)"
  RETRY="$(echo "$OUT" | grep -E "goto" | tail -n 1)"
  VERDICT="FAIL"
  if [ "$CODE" -eq 0 ]; then
    PASS=$((PASS + 1)); VERDICT="PASS"
  fi
  echo "RUN $i/$RUNS: $VERDICT (exit=$CODE)"
  echo "     last summary: $SUMMARY"
  if [ -n "$RETRY" ]; then echo "     goto retry: $RETRY"; fi
done

echo "----- summary -----"
echo "success rate: $PASS/$RUNS, failures: $((RUNS - PASS))"
echo "record template: | date | pass/total | marker | note |"
echo "===== measure done ====="