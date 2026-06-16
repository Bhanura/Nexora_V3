param(
    [switch]$Detach = $true
)

Write-Host "Starting local dev services: MongoDB + Qdrant"

$composeFile = "docker-compose.dev.yml"
$envFile = ".env.local"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Please install Docker Desktop and ensure 'docker' is on PATH."
    exit 1
}

if ($Detach) {
    docker compose -f $composeFile --env-file $envFile up -d
} else {
    docker compose -f $composeFile --env-file $envFile up
}

Write-Host "To stop: docker compose -f $composeFile down"
