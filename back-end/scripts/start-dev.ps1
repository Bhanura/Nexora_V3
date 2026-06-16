# Start local dev environment: MongoDB + Qdrant + Backend API
# Usage: .\scripts\start-dev.ps1

param(
    [switch]$Frontend = $false,
    [switch]$DetachDB = $true
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Nexora001 Dev Environment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Load .env.local
$envFile = ".env.local"
if (Test-Path $envFile) {
    Write-Host "`n[1/3] Loading environment from $envFile..." -ForegroundColor Yellow
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value)
        }
    }
    Write-Host "✓ Environment loaded" -ForegroundColor Green
} else {
    Write-Host "⚠ $envFile not found!" -ForegroundColor Yellow
    exit 1
}

# Start MongoDB + Qdrant
Write-Host "`n[2/3] Starting MongoDB + Qdrant..." -ForegroundColor Yellow
$composeFile = "docker-compose.dev.yml"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker not found" -ForegroundColor Red
    exit 1
}

if ($DetachDB) {
    docker compose -f $composeFile --env-file $envFile up -d
    Write-Host "✓ MongoDB + Qdrant started (detached)" -ForegroundColor Green
    Write-Host "  View logs: docker compose -f $composeFile logs -f" -ForegroundColor Cyan
} else {
    Write-Host "Starting in foreground (Ctrl+C to stop)..." -ForegroundColor Gray
    docker compose -f $composeFile --env-file $envFile up
}

# Start Backend API
Write-Host "`n[3/3] Starting Backend API..." -ForegroundColor Yellow
Write-Host "  MongoDB: $env:MONGODB_URI" -ForegroundColor Gray
Write-Host "  Qdrant: $env:QDRANT_URL" -ForegroundColor Gray
Write-Host "" -ForegroundColor Gray

python run_api.py

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Nexora001 Dev Environment Ready" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "`nTo stop DB: docker compose -f $composeFile down" -ForegroundColor Yellow
