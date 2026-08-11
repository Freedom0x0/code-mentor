#!/usr/bin/env bash
# evals/run.sh — 跑 evals/evals.json
#
# 用法：
#   ./evals/run.sh                 # 跑全部评测
#   ./evals/run.sh --id 1 2 3      # 只跑指定 id
#   ./evals/run.sh --dry           # 不调 Claude，只列 prompt（dry run）
#
# 除 --dry 外需要：本地有 claude CLI（`which claude` 能找到），且 SKILL.md 已被 cp -r 到 ~/.claude/skills/code-mentor/。
# judge 模式：把每条 prompt 直接喂给 Claude CLI，让它在 mentor 模式下回答；本脚本仅打印 CLI 输出，不自动判 PASS/FAIL（人工阅）。
#
# 退出码：0=全部调完；1=有 CLI 调用失败。

set -euo pipefail
cd "$(dirname "$0")/.."

DRY=0
IDS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry) DRY=1; shift ;;
    --id)
      shift
      [[ $# -gt 0 && "$1" != --* ]] || { echo "--id requires at least one eval id" >&2; exit 2; }
      while [[ $# -gt 0 && "$1" != --* ]]; do IDS+=("$1"); shift; done
      ;;
    --help|-h) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ "$DRY" != 1 ]] && ! command -v claude >/dev/null 2>&1; then
  echo "❌ 未检测到 claude CLI。请先安装 Claude Code。" >&2
  exit 1
fi

if [[ ! -f ~/.claude/skills/code-mentor/SKILL.md ]]; then
  echo "⚠️  ~/.claude/skills/code-mentor/SKILL.md 不存在，先 cp -r ./code-mentor ~/.claude/skills/" >&2
fi

# 解析 evals.json 拿 ids + 字段
read_ids() {
  EVAL_IDS="$(IFS=,; printf '%s' "${IDS[*]}")" python - <<'PY'
import json
import os

data = json.load(open('evals/evals.json', encoding='utf-8'))
raw_ids = os.environ.get('EVAL_IDS', '')
keep = {int(value) for value in raw_ids.split(',') if value} if raw_ids else None
for evaluation in data['evals']:
    if keep and evaluation['id'] not in keep:
        continue
    print(f"{evaluation['id']}|{evaluation['name']}|{evaluation['prompt']}")
PY
}

PASS=0
FAIL=0
TOTAL=0
while IFS='|' read -r id name prompt; do
  TOTAL=$((TOTAL+1))
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Eval #$id · $name"
  echo "Prompt: $prompt"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  if [[ "$DRY" == 1 ]]; then
    echo "(dry run — 跳过 Claude CLI)"
    PASS=$((PASS+1))
    continue
  fi
  # 调用 Claude CLI：把 prompt 当用户消息；带 system-prompt = 当前 SKILL.md
  if claude --system-prompt-file SKILL.md -p "$prompt" 2>&1 | tee "/tmp/eval-${id}.out"; then
    PASS=$((PASS+1))
  else
    FAIL=$((FAIL+1))
    echo "⚠️  eval #$id CLI 调用失败"
  fi
done < <(read_ids)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Done · total=$TOTAL ok=$PASS fail=$FAIL"
echo "输出文件：/tmp/eval-<id>.out"
echo "判定：人工对照 evals.json 的 expected_output 字段；建议对照 CASES.md 同 TC 号。"
exit "$FAIL"
