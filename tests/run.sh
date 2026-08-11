#!/usr/bin/env bash
# tests/run.sh — 跑 tests/CASES.md 表格 + tests/tc*.md 文件
#
# 用法：
#   ./tests/run.sh                  # 跑独立 tc 文件与 CASES-only 用例
#   ./tests/run.sh --files-only     # 只跑有独立 .md 文件的 tc
#   ./tests/run.sh --id 1           # 只跑 TC1（要求有独立 .md 文件）
#   ./tests/run.sh --dry            # dry run
#
# 与 evals/run.sh 的区别：本脚本跑的"压测 prompt"是给 Claude 的真实演练（不是用户首次提问），
# 内容来自 tests/tc<NN>-*.md 文件的正文；CASES-only 的 TC（无独立文件）从 CASES.md 表体提取 Scenario 列。
#
# 除 --dry 外需要：本地有 claude CLI。

set -euo pipefail
cd "$(dirname "$0")/.."

DRY=0
FILES_ONLY=0
IDS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry) DRY=1; shift ;;
    --files-only) FILES_ONLY=1; shift ;;
    --id)
      shift
      [[ $# -gt 0 && "$1" != --* ]] || { echo "--id requires at least one test id" >&2; exit 2; }
      while [[ $# -gt 0 && "$1" != --* ]]; do IDS+=("$1"); shift; done
      ;;
    --help|-h) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ "$DRY" != 1 ]] && ! command -v claude >/dev/null 2>&1; then
  echo "❌ 未检测到 claude CLI。" >&2
  exit 1
fi

# 1) 列有独立 .md 的 TC（按 tc 文件名排序）
TASKS=()
for f in tests/tc*.md; do
  [ -f "$f" ] || continue
  num=$(basename "$f" | sed -E 's/tc([0-9]+).*/\1/')
  # 把前导 0 去掉
  num=$((10#$num))
  TASKS+=("$num|file|$f")
done

# 2) 补充 CASES.md 中没有独立 .md 文件的用例。
if [[ "$FILES_ONLY" == 0 ]]; then
  while IFS=$'\t' read -r num scenario; do
    [[ -z "$num" || -z "$scenario" ]] && continue
    if ! compgen -G "tests/tc$(printf '%02d' "$num")-*.md" > /dev/null; then
      TASKS+=("$num|case|$scenario")
    fi
  done < <(
    awk '
      /^\|[[:space:]]*TC[0-9]+[[:space:]]*\|/ {
        line=$0
        sub(/^\|[[:space:]]*/, "", line)
        sub(/[[:space:]]*\|[[:space:]]*$/, "", line)
        id=line
        sub(/\|.*/, "", id)
        rest=line
        sub(/^[^|]*\|[[:space:]]*/, "", rest)
        expected=rest
        sub(/^.*\|[[:space:]]*/, "", expected)
        scenario=rest
        sub(/\|[^|]*$/, "", scenario)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", id)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", scenario)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", expected)
        sub(/^TC/, "", id)
        if (expected != "—") print id "\t" scenario
      }
    ' tests/CASES.md
  )
fi

# 3) 按 --id 过滤。
FILTERED=()
IFS=$'\n' TASKS_SORTED=($(printf '%s\n' "${TASKS[@]}" | sort -n))
unset IFS
for entry in "${TASKS_SORTED[@]}"; do
  num="${entry%%|*}"
  if [[ "${#IDS[@]}" -gt 0 ]]; then
    keep=no
    for id in "${IDS[@]}"; do
      [[ "$id" == "$num" ]] && keep=yes
    done
    [[ "$keep" == "no" ]] && continue
  fi
  FILTERED+=("$entry")
done

PASS=0
FAIL=0
for entry in "${FILTERED[@]}"; do
  IFS='|' read -r num source payload <<< "$entry"
  if [[ "$source" == "file" ]]; then
    label="$payload"
    prompt="$(cat "$payload")"
  else
    label="CASES.md"
    prompt="$payload"
  fi
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "TC$num — $label"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  if [[ "$DRY" == 1 ]]; then
    echo "Prompt: $prompt"
    echo "(dry run)"
    PASS=$((PASS+1))
    continue
  fi
  if claude --system-prompt-file SKILL.md -p "$prompt" 2>&1 | tee "/tmp/tc-${num}.out"; then
    PASS=$((PASS+1))
  else
    FAIL=$((FAIL+1))
    echo "⚠️  TC$num CLI 调用失败"
  fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Done · ok=$PASS fail=$FAIL"
echo "输出文件：/tmp/tc-<num>.out"
echo "判定：对照 CASES.md 同 TC 号 Expected behavior 列；找错处记下来。"
exit "$FAIL"
