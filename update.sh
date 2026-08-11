# code-mentor update script (bash / Git Bash / WSL / macOS / Linux)
# 从 git pull 后重新 cp skill 文件到 ~/.claude/skills/code-mentor/
#
# Usage:
#   bash update.sh
#
# 副作用:
#   - git pull origin <branch> 拉最新代码
#   - 重新 cp SKILL.md / README.md / evals/ / tests/ / assets/ 到 ~/.claude/skills/code-mentor/
#   - **不**触碰 ~/.claude/code-mentor/config.json（保留用户改过的 vault_path）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$SCRIPT_DIR"
SKILL_DST="$HOME/.claude/skills/code-mentor"
CONFIG_FILE="$HOME/.claude/code-mentor/config.json"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  code-mentor update"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 1) git pull
if [ -d "$SKILL_SRC/.git" ]; then
  BRANCH=$(git -C "$SKILL_SRC" symbolic-ref --short HEAD 2>/dev/null || echo "main")
  echo "→ git pull origin $BRANCH"
  git -C "$SKILL_SRC" pull --ff-only origin "$BRANCH" || {
    echo "  ⚠ git pull 失败（可能没设 upstream / 网络问题）。手动 cd $SKILL_SRC && git pull 再重跑。"
    exit 1
  }
  echo
else
  echo "⚠ $SKILL_SRC 不是 git 仓库，跳过 git pull（你需要手动 cd 到仓库跑 git pull）"
  echo
fi

# 2) 重新 cp skill 文件
if [ ! -d "$SKILL_DST" ]; then
  echo "✗ skill 未安装: $SKILL_DST"
  echo "  → 跑 ./setup.sh 先装"
  exit 1
fi

mkdir -p "$SKILL_DST"
cp "$SKILL_SRC/SKILL.md" "$SKILL_SRC/README.md" "$SKILL_DST/"
[ -d "$SKILL_SRC/evals" ]  && cp -r "$SKILL_SRC/evals"  "$SKILL_DST/"
[ -d "$SKILL_SRC/tests" ]  && cp -r "$SKILL_SRC/tests"  "$SKILL_DST/"
[ -d "$SKILL_SRC/assets" ] && cp -r "$SKILL_SRC/assets" "$SKILL_DST/"
echo "✓ skill 文件已更新: $SKILL_DST"
echo

# 3) 提示 config 没动
echo "⚠ 你的运行时配置保留不动: $CONFIG_FILE"
echo "  （vault_path 你之前填的不会被覆盖）"
echo
echo "升级完成。"