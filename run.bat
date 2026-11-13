@echo off
echo =========================================
echo Starting backend...
echo =========================================

start cmd /k "cd documentation-digester && uv run uvicorn documentation_digester.api.main:app --port 8000"

echo =========================================
echo Starting frontend...
echo =========================================

start cmd /k "cd frontend && npm run start"

echo =========================================
echo Both services started successfully.
echo =========================================