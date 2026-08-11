@echo off
REM code-mentor update script (Windows cmd)
REM 等价于 update.sh，cmd batch 语法。
REM
REM Usage:
REM   update.bat

setlocal

set "SCRIPT_DIR=%~dp0"
set "SKILL_SRC=%SCRIPT_DIR%"
set "SKILL_DST=%USERPROFILE%\.claude\skills\code-mentor"
set "CONFIG_FILE=%USERPROFILE%\.claude\code-mentor\config.json"

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   code-mentor update
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM 1) git pull
if exist "%SKILL_SRC%\.git" (
  for /f "delims=" %%b in ('git -C "%SKILL_SRC%" symbolic-ref --short HEAD 2^>nul') do set "BRANCH=%%b"
  if not defined BRANCH set "BRANCH=main"
  echo -^> git pull origin %BRANCH%
  pushd "%SKILL_SRC%"
  git pull --ff-only origin %BRANCH%
  if errorlevel 1 (
    popd
    echo   警告: git pull 失败。手动 cd 到仓库跑 git pull 再重跑。
    exit /b 1
  )
  popd
  echo.
) else (
  echo 警告: %SKILL_SRC% 不是 git 仓库，跳过 git pull
  echo.
)

REM 2) 重新 cp
if not exist "%SKILL_DST%" (
  echo X skill 未安装: %SKILL_DST%
  echo   -^> 跑 setup.bat 先装
  exit /b 1
)

if not exist "%SKILL_DST%" mkdir "%SKILL_DST%"
copy /Y "%SKILL_SRC%SKILL.md" "%SKILL_DST%\" >nul
copy /Y "%SKILL_SRC%README.md" "%SKILL_DST%\" >nul
if exist "%SKILL_SRC%evals"  xcopy /E /I /Y "%SKILL_SRC%evals"  "%SKILL_DST%\evals\"  >nul
if exist "%SKILL_SRC%tests"  xcopy /E /I /Y "%SKILL_SRC%tests"  "%SKILL_DST%\tests\"  >nul
if exist "%SKILL_SRC%assets" xcopy /E /I /Y "%SKILL_SRC%assets" "%SKILL_DST%\assets\" >nul
echo ✓ skill 文件已更新: %SKILL_DST%
echo.

REM 3) 提示 config 没动
echo 警告: 你的运行时配置保留不动: %CONFIG_FILE%
echo   （vault_path 你之前填的不会被覆盖）
echo.
echo 升级完成。

endlocal