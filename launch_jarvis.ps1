$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

Push-Location $Root
try {
    & $Python "launcher_bootstrap.py"
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
