param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8088,
    [string]$Model = "local-qwen-4b",
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string]$TTSEngine = "qwen3",
    [string]$QwenTTSBaseUrl = "http://127.0.0.1:5010",
    [string]$QwenTTSModel = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    [string]$QwenTTSVoice = "Sohee",
    [string]$OrpheusTTSBaseUrl = "http://127.0.0.1:5005",
    [string]$OrpheusTTSModel = "orpheus-3b-korean",
    [string]$OrpheusTTSVoice = "$([char]0xC720)$([char]0xB098)"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvPython = Join-Path $repoRoot "webvenv\Scripts\python.exe"
$localPython = Join-Path $env:LOCALAPPDATA "Python\bin\python.exe"

if (Test-Path -LiteralPath $venvPython) {
    $pythonExe = $venvPython
}
elseif (Test-Path -LiteralPath $localPython) {
    $pythonExe = $localPython
}
else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "Python was not found. Install Python or use the project's webvenv."
    }
    $pythonExe = $pythonCommand.Source
}

$env:LOCAL_LLM_API_HOST = $HostAddress
$env:LOCAL_LLM_API_PORT = [string]$Port
$env:LOCAL_LLM_MODEL = $Model
$env:OLLAMA_BASE_URL = $OllamaBaseUrl
$env:LOCAL_TTS_ENGINE = $TTSEngine
$env:QWEN_TTS_BASE_URL = $QwenTTSBaseUrl
$env:QWEN_TTS_MODEL = $QwenTTSModel
$env:QWEN_TTS_VOICE = $QwenTTSVoice
$env:ORPHEUS_TTS_BASE_URL = $OrpheusTTSBaseUrl
$env:ORPHEUS_TTS_MODEL = $OrpheusTTSModel
$env:ORPHEUS_TTS_VOICE = $OrpheusTTSVoice

& $pythonExe (Join-Path $PSScriptRoot "api_server.py")
