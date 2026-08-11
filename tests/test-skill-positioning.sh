#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 1) code-mentor 不能调外部 skill / 不依赖外部 skill 触发
for file in SKILL.md README.md evals/evals.json tests/CASES.md tests/tc*.md; do
  if grep -Eiq 'trellis|peaks-|knowledge skill|harness.{0,20}(match|trigger|inject)' "$file"; then
    echo "external skill reference remains in $file" >&2
    exit 1
  fi
done

# 2) code-mentor 不写代码 - SKILL.md 提到"写代码"时必须配合"不写/交给用户/陪你"否定语境
# 排除"不写代码 / 写代码是用户的活 / 你写代码 / mentor 写代码 →" 这类声明后，
# 仍出现裸"写代码"承诺 → 违规
if grep -nE '写代码|implement|TDD|tdd-workflow' SKILL.md \
    | grep -vE '不写代码|不是帮你写|不是替|不调外部|不替|写代码是用户|写代码的活|写代码 →|你写代码|用户的活' \
    | grep -q .; then
  echo "mentor 不写代码 — 但 SKILL.md 仍有裸的写代码承诺（不在不写/交给用户上下文中）" >&2
  exit 1
fi

# 3) 老项目三档停用已砍（v3.0 砍；v3.1 保持不引入）
if grep -Eq 'A 行级停用|B 新函数|C 新文件' SKILL.md; then
  echo "legacy tier system remains in SKILL.md" >&2
  exit 1
fi

# 4) knowledge vault 已集成到 code-mentor（不再依赖独立 skill）
# - SKILL.md 必须提到 vault_path / config.json 或 _drafts/
if ! grep -Eq 'vault_path|config\.json|_drafts/' SKILL.md; then
  echo "knowledge vault 集成约定缺失 in SKILL.md" >&2
  exit 1
fi

# 5) mentor 核心动作必须存在（v3.1 独有）
required=("认知陷阱" "梯度提问" "心智模型" "复盘" "沉淀" "复访")
for term in "${required[@]}"; do
  if ! grep -Fq "$term" SKILL.md; then
    echo "mentor 核心动作 '$term' 缺失 in SKILL.md" >&2
    exit 1
  fi
done

# 6) 4 mode 必须存在
required_modes=("观察" "讲解" "共学" "复盘")
for mode in "${required_modes[@]}"; do
  if ! grep -Fq "$mode" SKILL.md; then
    echo "mentor mode '$mode' 缺失 in SKILL.md" >&2
    exit 1
  fi
done

echo "skill positioning passed (v3.1 mentor, knowledge integrated, trellis free)"