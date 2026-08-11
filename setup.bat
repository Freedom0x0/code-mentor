@echo off
REM code-mentor setup script (Windows cmd)
REM 等价于 setup.sh，cmd batch 语法。
REM
REM Usage:
REM   setup.bat

setlocal

set "SCRIPT_DIR=%~dp0"
set "SKILL_SRC=%SCRIPT_DIR%"
set "SKILL_DST=%USERPROFILE%\.claude\skills\code-mentor"
set "CONFIG_DIR=%USERPROFILE%\.claude\code-mentor"
set "CONFIG_FILE=%CONFIG_DIR%\config.json"

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   code-mentor setup
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM 1) 装 skill
if exist "%SKILL_DST%" (
  echo ✓ skill 已存在: %SKILL_DST%（跳过复制，避免覆盖你手动改的内容）
  echo   -^> 跑 update.bat 升级
) else (
  mkdir "%SKILL_DST%"
  copy /Y "%SKILL_SRC%SKILL.md" "%SKILL_DST%\" >nul
  copy /Y "%SKILL_SRC%README.md" "%SKILL_DST%\" >nul
  if exist "%SKILL_SRC%evals"  xcopy /E /I /Y "%SKILL_SRC%evals"  "%SKILL_DST%\evals\"  >nul
  if exist "%SKILL_SRC%tests"  xcopy /E /I /Y "%SKILL_SRC%tests"  "%SKILL_DST%\tests\"  >nul
  if exist "%SKILL_SRC%assets" xcopy /E /I /Y "%SKILL_SRC%assets" "%SKILL_DST%\assets\" >nul
  echo ✓ skill 已安装: %SKILL_DST%
)
echo.

REM 2) 准备 config
if exist "%CONFIG_FILE%" (
  echo ✓ config 已存在: %CONFIG_FILE%（跳过；保留你填的 vault_path）
) else (
  mkdir "%CONFIG_DIR%" 2>nul
  (
    echo {
    echo   "_comment": "code-mentor 的运行时配置。第一次进 mentor 模式会引导你填。",
    echo   "vault_path": "<your-vault-path>",
    echo   "auto_invoke": false
    echo }
  ) > "%CONFIG_FILE%"
  echo ✓ config 已创建: %CONFIG_FILE%
  echo   警告: 你接下来要编辑这个文件，把 ^<your-vault-path^> 改成你的 Obsidian vault 绝对路径
)
echo.

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   你还需要手动做 3 件事
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo   1. 装 Obsidian（还没装的话）
echo        https://obsidian.md/
echo.
echo   2. 创建 vault，记下绝对路径
echo        Windows 示例: C:/Users/^<你^>/Documents/MyVault
echo.
echo   3. 编辑 config，把 vault_path 改成上面的路径
echo        notepad %CONFIG_FILE%
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   装完验证
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo   if exist %CONFIG_FILE% echo config 存在
echo   if exist "C:\path\to\your\vault" echo vault 路径有效
echo   if exist "%SKILL_DST%\SKILL.md" echo skill 已装
echo.
echo 进 Claude 加载 code-mentor skill 后，第一次进 mentor 模式会引导你跑一次。

endlocal