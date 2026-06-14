param(
    [int]$Port = 4173,
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Url = "http://127.0.0.1:$Port/"

Push-Location $Root
try {
    if (-not $NoOpen) {
        Start-Process $Url
    }
    Write-Host "Obsidian Workbench: $Url"
    python -m http.server $Port --bind 127.0.0.1
}
finally {
    Pop-Location
}
