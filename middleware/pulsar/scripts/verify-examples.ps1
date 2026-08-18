$ErrorActionPreference = "Stop"
$root = Join-Path $PSScriptRoot ".." "examples" "java"
Write-Host "Compiling all modules..."
Push-Location $root
mvn -q compile
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Maven compile failed - need JDK 8+ and Maven" }
Pop-Location
Write-Host "Compile OK. Run Testcontainers tests separately: cd examples/java/pulsar-basics; mvn test"
Write-Host "Requires Docker for integration test."
