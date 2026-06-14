param(
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Push-Location $Root
try {
    python .\tools\build_html.py
    $Index = Join-Path $Root "site\index.html"
    if (-not $NoOpen) {
        Start-Process $Index
    }
    Write-Host "HTML notebook is ready: $Index"
}
finally {
    Pop-Location
}
