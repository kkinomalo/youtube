param(
    [string]$BaseUrl = "http://127.0.0.1:8088/v1",
    [string]$Model = "local-qwen-4b",
    [int]$TTSTimeoutSec = 600,
    [string]$SystemPrompt = "You are a helpful local assistant. Answer in Korean unless the user asks otherwise. You are connected to a local TTS API outside the model. Do not suggest Google TTS, gTTS, Amazon Polly, or cloud TTS unless the user explicitly asks for cloud services. If the user asks to make speech or TTS, write only the text that should be synthesized; the host script will create the local WAV file."
)

$ErrorActionPreference = "Stop"

$apiRoot = $BaseUrl.TrimEnd("/") -replace "/v1$", ""
$lastAssistantText = ""

function Invoke-LocalTTS {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text,
        [string]$Voice = "Sohee",
        [int]$Rate = 8,
        [int]$TimeoutSec = 600
    )

    $ttsBody = @{
        text = $Text
        voice = $Voice
        rate = $Rate
    } | ConvertTo-Json

    Write-Host "Creating TTS: $Text"
    Write-Host "Qwen3-TTS first load can take several minutes. Please wait..."

    $ttsResponse = Invoke-RestMethod `
        -Method Post `
        -Uri "$apiRoot/tts" `
        -ContentType "application/json; charset=utf-8" `
        -Body $ttsBody `
        -TimeoutSec $TimeoutSec

    Write-Host "TTS saved: $($ttsResponse.audio_path)"
    Write-Host "TTS URL:   $apiRoot$($ttsResponse.audio_url)"

    if ($ttsResponse.audio_path -and (Test-Path -LiteralPath $ttsResponse.audio_path)) {
        Start-Process -FilePath $ttsResponse.audio_path
    }
}

function Test-TTSRequested {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    $patterns = @(
        "(?i)tts",
        "(?i)wav",
        "(?i)mp3",
        "(?i)voice",
        "(?i)speech",
        "(?i)audio",
        "\uC74C\uC131",
        "\uC18C\uB9AC",
        "\uC77D\uC5B4",
        "\uB9D0\uD574",
        "\uB179\uC74C",
        "\uBAA9\uC18C\uB9AC",
        "\uBCC0\uD658",
        "\uD30C\uC77C"
    )

    foreach ($pattern in $patterns) {
        if ($Text -match $pattern) {
            return $true
        }
    }

    return $false
}

function Get-DirectTTSText {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    $trimmed = $Text.Trim()

    if ($trimmed -match "^(?i)/tts\s+(.+)$") {
        return $Matches[1].Trim()
    }

    $quotePatterns = @(
        '"([^"]+)"',
        "'([^']+)'",
        "\u201C([^\u201D]+)\u201D",
        "\u2018([^\u2019]+)\u2019"
    )

    foreach ($pattern in $quotePatterns) {
        if ($trimmed -match $pattern) {
            return $Matches[1].Trim()
        }
    }

    if ($trimmed -match "[:\uFF1A]\s*(.+)$") {
        return $Matches[1].Trim()
    }

    return ""
}

$messages = New-Object System.Collections.Generic.List[object]
$messages.Add(@{
    role = "system"
    content = $SystemPrompt
})

Write-Host "Local LLM chat started. Model: $Model"
Write-Host "Commands: /reset, /exit, /tts, /tts <text>"
Write-Host "TTS runs only when your message explicitly asks for TTS/audio, or when you type /tts."
Write-Host ""

while ($true) {
    Write-Host -NoNewline "You> "
    $userInput = [Console]::ReadLine()

    if ([string]::IsNullOrWhiteSpace($userInput)) {
        continue
    }

    if ($userInput -eq "/exit") {
        break
    }

    if ($userInput -match "^(?i)/tts(\s+.*)?$") {
        $directText = Get-DirectTTSText -Text $userInput
        if (-not [string]::IsNullOrWhiteSpace($directText)) {
            Invoke-LocalTTS -Text $directText -TimeoutSec $TTSTimeoutSec
        }
        elseif ([string]::IsNullOrWhiteSpace($lastAssistantText)) {
            Write-Host "No assistant response to synthesize yet. Use: /tts text here"
        }
        else {
            Invoke-LocalTTS -Text $lastAssistantText -TimeoutSec $TTSTimeoutSec
        }
        continue
    }

    if ($userInput -eq "/reset") {
        $messages.Clear()
        $messages.Add(@{
            role = "system"
            content = $SystemPrompt
        })
        $lastAssistantText = ""
        Write-Host "Conversation reset."
        continue
    }

    if (Test-TTSRequested -Text $userInput) {
        $directText = Get-DirectTTSText -Text $userInput
        if (-not [string]::IsNullOrWhiteSpace($directText)) {
            try {
                Invoke-LocalTTS -Text $directText -TimeoutSec $TTSTimeoutSec
                Write-Host ""
            }
            catch {
                Write-Host "TTS failed: $($_.Exception.Message)"
                Write-Host "Check that Orpheus-FastAPI is running on http://127.0.0.1:5005 and this API is running on http://127.0.0.1:8088."
                Write-Host ""
            }
            continue
        }
    }

    $messages.Add(@{
        role = "user"
        content = $userInput
    })

    $body = @{
        model = $Model
        messages = $messages
        stream = $false
    } | ConvertTo-Json -Depth 20

    try {
        $response = Invoke-RestMethod `
            -Method Post `
            -Uri "$($BaseUrl.TrimEnd('/'))/chat/completions" `
            -ContentType "application/json; charset=utf-8" `
            -Body $body `
            -TimeoutSec 180

        $assistantText = $response.choices[0].message.content
        $lastAssistantText = $assistantText
        Write-Host ""
        Write-Host "Assistant: $assistantText"
        Write-Host ""

        $messages.Add(@{
            role = "assistant"
            content = $assistantText
        })

        if (Test-TTSRequested -Text $userInput) {
            try {
                Invoke-LocalTTS -Text $assistantText -TimeoutSec $TTSTimeoutSec
                Write-Host ""
            }
            catch {
                Write-Host "TTS failed: $($_.Exception.Message)"
                Write-Host ""
            }
        }
    }
    catch {
        Write-Host ""
        Write-Host "Request failed: $($_.Exception.Message)"
        Write-Host ""
        if ($messages.Count -gt 1) {
            $messages.RemoveAt($messages.Count - 1)
        }
    }
}
