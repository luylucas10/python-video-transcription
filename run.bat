@echo off
setlocal
cd /d "%~dp0"
call ".venv\Scripts\activate.bat"
python -m video_to_text
set "exit_code=%ERRORLEVEL%"
echo.
echo Execucao finalizada com codigo %exit_code%.
pause
exit /b %exit_code%

