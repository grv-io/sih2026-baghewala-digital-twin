# Local dev runner (Windows PowerShell). Serves the API + dashboard on one
# process at http://127.0.0.1:8000/ -- see docs/DEPLOY.md "local run".
#
# Usage:
#   .\scripts\dev.ps1            # rebuild the dashboard, then run the server
#   .\scripts\dev.ps1 -NoBuild   # skip the dashboard rebuild
#   .\scripts\dev.ps1 -Port 8080

param(
    [switch]$NoBuild,
    [int]$Port = 8000
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "No .venv found at $Python -- create it first: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}

if (-not $NoBuild) {
    $Node = "node"
    Write-Host "Rebuilding dashboard..."
    & $Node (Join-Path $RepoRoot "dashboard\build.js")
}

$env:PORT = "$Port"
Write-Host "Starting API + dashboard on http://127.0.0.1:$Port/ (Ctrl+C to stop)"
& $Python -m uvicorn api.main:app --reload --host 127.0.0.1 --port $Port --app-dir $RepoRoot
