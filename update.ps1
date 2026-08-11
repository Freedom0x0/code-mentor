# code-mentor update script (Windows PowerShell)
# 等价于 update.sh，PowerShell 语法。
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File update.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillSrc  = $ScriptDir
$SkillDst  = Join-Path $env:USERPROFILE ".claude\skills\code-mentor"
$ConfigFile = Join-Path $env:USERPROFILE ".claude\code-mentor\config.json"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  code-mentor update"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

# 1) git pull
if (Test-Path (Join-Path $SkillSrc ".git")) {
  Push-Location $SkillSrc
  $Branch = & git symbolic-ref --short HEAD 2>$null
  if (-not $Branch) { $Branch = "main" }
  Write-Host "→ git pull origin $Branch"
  & git pull --ff-only origin $Branch
  if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Host "  ⚠ git pull 失败（可能没设 upstream / 网络问题）。手动 cd 到仓库跑 git pull 再重跑。"
    exit 1
  }
  Pop-Location
  Write-Host ""
} else {
  Write-Host "⚠ $ScriptDir 不是 git 仓库，跳过 git pull"
  Write-Host ""
}

# 2) 重新 cp
if (-not (Test-Path $SkillDst)) {
  Write-Host "✗ skill 未安装: $SkillDst"
  Write-Host "  → 跑 .\setup.ps1 先装"
  exit 1
}

New-Item -ItemType Directory -Force -Path $SkillDst | Out-Null
Copy-Item -Path (Join-Path $SkillSrc "SKILL.md") -Destination $SkillDst -Force
Copy-Item -Path (Join-Path $SkillSrc "README.md") -Destination $SkillDst -Force
if (Test-Path (Join-Path $SkillSrc "evals"))  { Copy-Item -Path (Join-Path $SkillSrc "evals")  -Recurse -Force -Destination $SkillDst }
if (Test-Path (Join-Path $SkillSrc "tests"))  { Copy-Item -Path (Join-Path $SkillSrc "tests")  -Recurse -Force -Destination $SkillDst }
if (Test-Path (Join-Path $SkillSrc "assets")) { Copy-Item -Path (Join-Path $SkillSrc "assets") -Recurse -Force -Destination $SkillDst }
Write-Host "✓ skill 文件已更新: $SkillDst"
Write-Host ""

# 3) 提示 config 没动
Write-Host "⚠ 你的运行时配置保留不动: $ConfigFile"
Write-Host "  （vault_path 你之前填的不会被覆盖）"
Write-Host ""
Write-Host "升级完成。"