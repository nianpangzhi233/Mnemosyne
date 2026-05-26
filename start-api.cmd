@echo off
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set HF_ENDPOINT=https://hf-mirror.com

echo ==========================================
echo  Mnemosyne Legacy REST API
echo ==========================================
echo.
echo  Legacy API: http://localhost:8979/api/health
echo  V8 API:     http://localhost:8979/api/v8/health
echo  Swagger: http://localhost:8979/docs
echo.

echo  Prefer start-v8-api.cmd for new work.

python "%~dp0scripts\api\start_api.py" --port 8979
