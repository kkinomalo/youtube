param(
    [string]$Model = "qwen3:4b",
    [string]$Alias = "local-qwen-4b",
    [int]$Context = 8192,
    [string]$HostAddress = "0.0.0.0:11434",
    [switch]$SkipPull,
    [switch]$SkipAlias,
    [switch]$SkipProbe
)

$ErrorActionPreference = "Stop"

function Test-OllamaHttp {
    try {
        Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3 | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

$ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
$ollamaExe = $null
if ($ollamaCommand) {
    $ollamaExe = $ollamaCommand.Source
}

if (-not $ollamaExe) {
    $candidate = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
    if (Test-Path -LiteralPath $candidate) {
        $ollamaExe = $candidate
    }
}

if (-not $ollamaExe) {
    throw "Ollama is not installed or is not on PATH. Install it from https://ollama.com/download, then rerun this script."
}

$env:OLLAMA_HOST = $HostAddress

if (-not (Test-OllamaHttp)) {
    Write-Host "Starting Ollama on $HostAddress ..."
    Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden

    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        if (Test-OllamaHttp) {
            $ready = $true
            break
        }
    }

    if (-not $ready) {
        throw "Ollama did not become ready on http://127.0.0.1:11434."
    }
}

$models = & $ollamaExe list
$hasModel = $models -match [regex]::Escape($Model)

if (-not $hasModel -and -not $SkipPull) {
    Write-Host "Pulling $Model ..."
    & $ollamaExe pull $Model
}
elseif (-not $hasModel) {
    Write-Warning "$Model is not installed, and -SkipPull was set."
}

if (-not $SkipAlias) {
    $safeAlias = $Alias -replace '[^A-Za-z0-9_.-]', '-'
    $modelfile = Join-Path $env:TEMP "ollama-$safeAlias-Modelfile"
    @"
FROM $Model
PARAMETER num_ctx $Context
PARAMETER temperature 0.2
PARAMETER top_p 0.9
SYSTEM You are a local coding and CTF assistant. Be concise, accurate, and explicit about uncertainty.
"@ | Set-Content -LiteralPath $modelfile -Encoding UTF8

    Write-Host "Creating Ollama alias $Alias with num_ctx=$Context ..."
    & $ollamaExe create $Alias -f $modelfile
}

if (-not $SkipProbe) {
    $body = @{
        model = $Alias
        messages = @(
            @{
                role = "user"
                content = "Answer in one short sentence: is the local LLM API ready?"
            }
        )
        stream = $false
    } | ConvertTo-Json -Depth 10

    Write-Host "Probing OpenAI-compatible API ..."
    $response = Invoke-RestMethod `
        -Method Post `
        -Uri "http://127.0.0.1:11434/v1/chat/completions" `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 120

    $response.choices[0].message.content
}

Write-Host ""
Write-Host "Ready:"
Write-Host "  Base URL: http://127.0.0.1:11434/v1/"
Write-Host "  Model:    $Alias"
Write-Host "  LAN URL:  http://<server-ip>:11434/v1/chat/completions"
