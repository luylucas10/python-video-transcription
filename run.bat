@echo off
setlocal
cd /d "%~dp0"
uv run python -m video_to_text %*
set "exit_code=%ERRORLEVEL%"
echo.
echo Execucao finalizada com codigo %exit_code%.
pause
exit /b %exit_code%
