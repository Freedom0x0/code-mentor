# code-mentor setup script (Windows PowerShell)
# 等价于 setup.sh，PowerShell 语法。
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File setup.ps1
# 或在 PowerShell 里：
#   .\setup.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillSrc  = $ScriptDir
$SkillDst  = Join-Path $env:USERPROFILE ".claude\skills\code-mentor"
$ConfigDir = Join-Path $env:USERPROFILE ".claude\code-mentor"
$ConfigFile = Join-Path $ConfigDir "config.json"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  code-mentor setup"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

# 1) 装 skill
if (Test-Path $SkillDst) {
  Write-Host "✓ skill 已存在: $SkillDst（跳过复制，避免覆盖你手动改的内容）"
  Write-Host "  → 跑 .\update.ps1 升级"
} else {
  New-Item -ItemType Directory -Force -Path $SkillDst | Out-Null
  Copy-Item -Path (Join-Path $SkillSrc "SKILL.md") -Destination $SkillDst
  Copy-Item -Path (Join-Path $SkillSrc "README.md") -Destination $SkillDst
  if (Test-Path (Join-Path $SkillSrc "evals"))  { Copy-Item -Path (Join-Path $SkillSrc "evals")  -Recurse -Destination $SkillDst }
  if (Test-Path (Join-Path $SkillSrc "tests"))  { Copy-Item -Path (Join-Path $SkillSrc "tests")  -Recurse -Destination $SkillDst }
  if (Test-Path (Join-Path $SkillSrc "assets")) { Copy-Item -Path (Join-Path $SkillSrc "assets") -Recurse -Destination $SkillDst }
  Write-Host "✓ skill 已安装: $SkillDst"
}
Write-Host ""

# 2) 准备 config
if (Test-Path $ConfigFile) {
  Write-Host "✓ config 已存在: $ConfigFile（跳过；保留你填的 vault_path）"
} else {
  New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
  @"
{
  "_comment": "code-mentor 的运行时配置。第一次进 mentor 模式会引导你填。",
  "vault_path": "<your-vault-path>",
  "auto_invoke": false
}
"@ | Set-Content -Path $ConfigFile -Encoding UTF8
  Write-Host "✓ config 已创建: $ConfigFile"
  Write-Host "  ⚠ 你接下来要编辑这个文件，把 <your-vault-path> 改成你的 Obsidian vault 绝对路径"
}
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  你还需要手动做 3 件事"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""
Write-Host "  1. 装 Obsidian（还没装的话）"
Write-Host "       https://obsidian.md/"
Write-Host ""
Write-Host "  2. 创建 vault，记下绝对路径"
Write-Host "       Windows 示例: C:/Users/<你>/Documents/MyVault"
Write-Host ""
Write-Host "  3. 编辑 config，把 vault_path 改成上面的路径"
Write-Host "       notepad $ConfigFile"
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  装完验证"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""
Write-Host "  Test-Path $ConfigFile"
Write-Host "  Test-Path <vault 绝对路径>"
Write-Host "  Test-Path (Join-Path $SkillDst 'SKILL.md')"
Write-Host ""
Write-Host "进 Claude 加载 code-mentor skill 后，第一次进 mentor 模式会引导你跑一次。"