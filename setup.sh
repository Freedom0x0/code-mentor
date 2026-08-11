#!/usr/bin/env bash
# code-mentor setup script (bash / Git Bash / WSL / macOS / Linux)
# 把 skill 装到 ~/.claude/skills/code-mentor/，准备 config.json，打印剩余手动步骤
#
# Usage:
#   bash setup.sh
#
# 副作用:
#   - 创建 ~/.claude/skills/code-mentor/ 目录（如不存在）
#   - 创建 ~/.claude/code-mentor/ 目录
#   - 复制 SKILL.md / README.md / evals/ / tests/ / assets/ 到 ~/.claude/skills/code-mentor/
#   - 复制 config.example.json 到 ~/.claude/code-mentor/config.json（如果不存在）
#   - 不创建 vault、不写 vault_path（需要用户手动填）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$SCRIPT_DIR"
SKILL_DST="$HOME/.claude/skills/code-mentor"
CONFIG_DIR="$HOME/.claude/code-mentor"
CONFIG_FILE="$CONFIG_DIR/config.json"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  code-mentor setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 1) 装 skill 文件
if [ -d "$SKILL_DST" ]; then
  echo "✓ skill 已存在: $SKILL_DST（跳过复制，避免覆盖你手动改的内容）"
  echo "  → 跑 ./update.sh 升级"
else
  mkdir -p "$SKILL_DST"
  # 排除 .git / .darwin / .gitignore / docs / test-prompts.json（开发资产不进运行时）
  cp "$SKILL_SRC/SKILL.md" "$SKILL_SRC/README.md" "$SKILL_DST/"
  [ -d "$SKILL_SRC/evals" ]   && cp -r "$SKILL_SRC/evals"   "$SKILL_DST/"
  [ -d "$SKILL_SRC/tests" ]   && cp -r "$SKILL_SRC/tests"   "$SKILL_DST/"
  [ -d "$SKILL_SRC/assets" ]  && cp -r "$SKILL_SRC/assets"  "$SKILL_DST/"
  echo "✓ skill 已安装: $SKILL_DST"
fi
echo

# 2) 准备 config
if [ -f "$CONFIG_FILE" ]; then
  echo "✓ config 已存在: $CONFIG_FILE（跳过；保留你填的 vault_path）"
else
  mkdir -p "$CONFIG_DIR"
  cat > "$CONFIG_FILE" <<'JSON'
{
  "_comment": "code-mentor 的运行时配置。第一次进 mentor 模式会引导你填。",
  "vault_path": "<your-vault-path>",
  "auto_invoke": false
}
JSON
  echo "✓ config 已创建: $CONFIG_FILE"
  echo "  ⚠ 你接下来要编辑这个文件，把 <your-vault-path> 改成你的 Obsidian vault 绝对路径"
fi
echo

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  你还需要手动做 3 件事"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "  1. 装 Obsidian（还没装的话）"
echo "       https://obsidian.md/"
echo
echo "  2. 创建 vault，记下绝对路径"
echo "       Windows 示例: C:/Users/<你>/Documents/MyVault"
echo "       macOS/Linux 示例: /Users/<你>/Documents/MyVault"
echo
echo "  3. 编辑 config，把 vault_path 改成上面的路径"
echo "       code $CONFIG_FILE"
echo "       或 notepad $CONFIG_FILE (Windows cmd)"
echo "       或 \$EDITOR $CONFIG_FILE (bash)"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  装完验证"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "  [ -f $CONFIG_FILE ] && echo 'config 存在'"
echo "  vault 目录存在 && echo 'vault 路径有效'"
echo "  $SKILL_DST/SKILL.md 存在 && echo 'skill 已装'"
echo
echo "进 Claude 加载 code-mentor skill 后，第一次进 mentor 模式会引导你跑一次。"

# macOS: $EDITOR 没设时给个友好的 fallback
echo
echo "提示: macOS / Linux 如果 \$EDITOR 没设，直接 \$EDITOR=$CONFIG_FILE bash 起来再打开。
"