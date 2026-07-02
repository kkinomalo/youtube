param(
    [string]$TargetUrl = "http://127.0.0.1:8088",
    [string]$HealthPath = "/health"
)

$ErrorActionPreference = "Stop"

function Find-Zrok {
    $candidates = @(
        "zrok2",
        "zrok",
        (Join-Path $env:USERPROFILE "bin\zrok2.exe"),
        (Join-Path $env:USERPROFILE "bin\zrok.exe")
    )

    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return $command.Source
        }

        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    throw "zrok2 was not found. Install zrok2 first, then run: zrok2 enable <token>"
}

$target = $TargetUrl.TrimEnd("/")
$healthUrl = "$target$HealthPath"

Write-Host "Checking local API: $healthUrl"
try {
    Invoke-RestMethod -Method Get -Uri $healthUrl -TimeoutSec 5 | Out-Null
}
catch {
    throw "Local API is not reachable at $healthUrl. Start local-llm\Start-LocalLLMApi.ps1 first."
}

$zrokExe = Find-Zrok
Write-Host "Starting zrok public share for: $target"
Write-Host ""
Write-Host "Copy the *.shares.zrok.io URL shown below and send it to the full-stack developer."
Write-Host "Press Ctrl+C here when you want to stop sharing."
Write-Host ""

& $zrokExe share public $target
