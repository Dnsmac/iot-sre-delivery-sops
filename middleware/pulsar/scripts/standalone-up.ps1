$dockerDir = Join-Path $PSScriptRoot ".." "docker"
Set-Location $dockerDir
docker compose -f docker-compose-standalone.yml up -d
Write-Host "Pulsar Standalone: pulsar://localhost:6650  Admin: http://localhost:8080"
docker compose -f docker-compose-standalone.yml ps
