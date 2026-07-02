param(
    [string]$BaseUrl = "http://127.0.0.1:8088",
    [string]$Text = "$([char]0xC548)$([char]0xB155)$([char]0xD558)$([char]0xC138)$([char]0xC694). Qwen3 12Hz 0.6B AI TTS API $([char]0xD14C)$([char]0xC2A4)$([char]0xD2B8)$([char]0xC785)$([char]0xB2C8)$([char]0xB2E4).",
    [string]$Voice = "Sohee",
    [int]$Rate = 8,
    [string]$OutFile = ".\local-llm\tts-output.wav"
)

$ErrorActionPreference = "Stop"

$body = @{
    text = $Text
    voice = $Voice
    rate = $Rate
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Method Post `
    -Uri "$($BaseUrl.TrimEnd('/'))/tts" `
    -ContentType "application/json; charset=utf-8" `
    -Body $body `
    -TimeoutSec 600

$audioUrl = "$($BaseUrl.TrimEnd('/'))$($response.audio_url)"
Invoke-WebRequest -Uri $audioUrl -OutFile $OutFile | Out-Null

Write-Host "TTS response:"
$response
Write-Host ""
Write-Host "Saved audio: $OutFile"
Start-Process -FilePath $OutFile
