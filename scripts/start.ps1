#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start CodeSentinel locally — Redis, Qdrant, FastAPI backend, Celery worker, Next.js frontend, ngrok.
.USAGE
    .\start.ps1
#>

$ROOT = Split-Path $PSScriptRoot -Parent
$BACKEND = Join-Path $ROOT "backend"
$FRONTEND = Join-Path $ROOT "frontend"
$LOGS = Join-Path $ROOT ".logs"

# Create logs dir
New-Item -ItemType Directory -Path $LOGS -Force | Out-Null

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CodeSentinel — Starting All Services  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Redis ──────────────────────────────────────────────────────────────────
Write-Host "[1/6] Starting Redis..." -ForegroundColor Yellow
if (Test-Path "C:\redis\redis-server.exe") {
    Start-Process -FilePath "C:\redis\redis-server.exe" `
        -WindowStyle Hidden `
        -RedirectStandardOutput "$LOGS\redis.log" `
        -RedirectStandardError "$LOGS\redis.err"
    Write-Host "      Redis started on port 6379" -ForegroundColor Green
} else {
    Write-Host "      WARNING: redis-server.exe not found at C:\redis. Celery will fail." -ForegroundColor Red
}

# ── 2. Qdrant ─────────────────────────────────────────────────────────────────
Write-Host "[2/6] Starting Qdrant..." -ForegroundColor Yellow
if (Test-Path "C:\qdrant\qdrant.exe") {
    Start-Process -FilePath "C:\qdrant\qdrant.exe" `
        -WindowStyle Hidden `
        -RedirectStandardOutput "$LOGS\qdrant.log" `
        -RedirectStandardError "$LOGS\qdrant.err"
    Write-Host "      Qdrant started on port 6333" -ForegroundColor Green
} else {
    Write-Host "      WARNING: qdrant.exe not found at C:\qdrant." -ForegroundColor Red
}

Start-Sleep -Seconds 3

# ── 3. FastAPI Backend ────────────────────────────────────────────────────────
Write-Host "[3/6] Starting FastAPI backend..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" `
    -ArgumentList "-NoProfile", "-Command", "cd '$BACKEND'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 2>&1 | Tee-Object -FilePath '$LOGS\backend.log'" `
    -WindowStyle Normal

Write-Host "      Backend starting on http://localhost:8000" -ForegroundColor Green

Start-Sleep -Seconds 4

# ── 4. Celery Worker ──────────────────────────────────────────────────────────
Write-Host "[4/6] Starting Celery worker..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" `
    -ArgumentList "-NoProfile", "-Command", "cd '$BACKEND'; python -m celery -A workers.celery_app worker --loglevel=info -Q scans 2>&1 | Tee-Object -FilePath '$LOGS\celery.log'" `
    -WindowStyle Normal

Write-Host "      Celery worker started" -ForegroundColor Green

# ── 5. Next.js Frontend ───────────────────────────────────────────────────────
Write-Host "[5/6] Starting Next.js frontend..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" `
    -ArgumentList "-NoProfile", "-Command", "cd '$FRONTEND'; npm run dev 2>&1 | Tee-Object -FilePath '$LOGS\frontend.log'" `
    -WindowStyle Normal

Write-Host "      Frontend starting on http://localhost:3000" -ForegroundColor Green

Start-Sleep -Seconds 5

# ── 6. ngrok ─────────────────────────────────────────────────────────────────
Write-Host "[6/6] Starting ngrok tunnel for webhook endpoint..." -ForegroundColor Yellow
Start-Process -FilePath "ngrok" `
    -ArgumentList "http", "8000", "--log=stdout" `
    -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All services launched!" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host "  Qdrant UI:    http://localhost:6333/dashboard" -ForegroundColor White
Write-Host "  ngrok URL:    http://localhost:4040  (inspect tunnel)" -ForegroundColor White
Write-Host ""
Write-Host "  Use the ngrok URL as your GitHub Webhook Payload URL:" -ForegroundColor Yellow
Write-Host "  https://<your-ngrok-id>.ngrok-free.app/webhooks/github" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Logs saved to: $LOGS" -ForegroundColor Gray
