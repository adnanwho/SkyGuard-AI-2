@echo off
setlocal
cd /d "%~dp0"
echo ================================================
echo SkyGuard AI - Prototype Demo
echo ================================================
echo Starting local dashboard server...
start "SkyGuard AI Server" /min cmd /k "cd /d ""%~dp0"" && (py -3 server.py --host 127.0.0.1 --port 8137 || python server.py --host 127.0.0.1 --port 8137)"
timeout /t 3 /nobreak >nul
start "SkyGuard AI Dashboard" http://127.0.0.1:8137/
echo.
echo Dashboard: http://127.0.0.1:8137/
echo Keep the minimized SkyGuard AI Server window open while presenting.
echo Close that server window when finished.
pause
endlocal
