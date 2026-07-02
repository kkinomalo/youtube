param(
    [int]$Port = 5010,
    [switch]$Build
)

$ErrorActionPreference = "Stop"

$composeFile = Join-Path $PSScriptRoot "docker-compose.qwen-tts.yaml"
if (-not (Test-Path -LiteralPath $composeFile)) {
    throw "Compose file was not found: $composeFile"
}

$env:QWEN_TTS_PORT = [string]$Port

Push-Location $PSScriptRoot
try {
    if ($Build) {
        docker compose -f $composeFile up -d --build
    }
    else {
        docker compose -f $composeFile up -d
    }
}
finally {
    Pop-Location
}

Write-Host "Waiting for Qwen3-TTS on http://127.0.0.1:$Port ..."
$deadline = (Get-Date).AddMinutes(3)
do {
    try {
        $health = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 5
        if ($health.status -eq "ok") {
            Write-Host "Qwen3-TTS API is listening on http://127.0.0.1:$Port"
            Write-Host "Model: $($health.model)"
            Write-Host "Note: first TTS request downloads/loads the model and can take several minutes."
            exit 0
        }
    }
    catch {
    }
    Start-Sleep -Seconds 5
} while ((Get-Date) -lt $deadline)

Write-Host "Qwen3-TTS did not open port $Port yet. Recent logs:"
docker compose -f $composeFile ps
docker compose -f $composeFile logs --tail 80
exit 1
