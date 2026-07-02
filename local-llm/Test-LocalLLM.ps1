param(
    [string]$Model = "local-qwen-4b",
    [string]$BaseUrl = "http://127.0.0.1:11434/v1",
    [string]$Prompt = "Answer briefly: is this local API working?"
)

$ErrorActionPreference = "Stop"

$body = @{
    model = $Model
    messages = @(
        @{
            role = "system"
            content = "You are a concise local assistant."
        },
        @{
            role = "user"
            content = $Prompt
        }
    )
    stream = $false
} | ConvertTo-Json -Depth 10

$uri = "$($BaseUrl.TrimEnd('/'))/chat/completions"
$response = Invoke-RestMethod -Method Post -Uri $uri -ContentType "application/json" -Body $body -TimeoutSec 120

$response.choices[0].message.content
