@echo off
echo ============================================================
echo  PeopleOS Backend — Setup and Start
echo ============================================================

:: Add PostgreSQL to PATH
set PATH=%PATH%;C:\Program Files\PostgreSQL\18\bin

:: Create database if not exists
echo [1/4] Creating database...
set PGPASSWORD=root
psql -U postgres -h localhost -c "CREATE DATABASE peopleos;" 2>nul
echo     Done (or already exists)

:: Install dependencies
echo [2/4] Installing Python dependencies...
C:\Python314\python.exe -m pip install -r requirements.txt -q
echo     Done

:: Run seed script
echo [3/4] Seeding database...
C:\Python314\python.exe seed.py

:: Start server
echo [4/4] Starting FastAPI server...
C:\Python314\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
