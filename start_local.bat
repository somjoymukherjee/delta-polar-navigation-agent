@echo off
title DeLTa AI Platform Launcher
echo ========================================================
echo   Launching DeLTa Antarctic Intelligence Platform
echo ========================================================
echo.

echo [1/3] Starting Backend API (FastAPI) on port 8000...
start "DeLTa Backend" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Starting Frontend Dev Server (Vite) on port 5173...
start "DeLTa Frontend" cmd /k "cd frontend && npm run dev"

echo [3/3] Waiting for services to initialize...
timeout /t 3 /nobreak >nul

echo Opening browser at http://localhost:5173/ ...
start http://localhost:5173/

echo.
echo ========================================================
echo   DeLTa Platform is running!
echo   Local URL:    http://localhost:5173/
echo   API Docs:     http://localhost:8000/docs
echo ========================================================
