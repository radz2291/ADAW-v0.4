param(
    [string]$Project = ".local/g1-night-circuit-v2",
    [ValidateRange(1, 65535)]
    [int]$Port = 8765,
    [switch]$ApiOnly
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Set up the repository environment using tools/setup.ps1 first."
}

Push-Location -LiteralPath $repo
try {
    $arguments = @("-m", "app.studio_api", "--root", $Project, "--port", $Port)
    if ($ApiOnly) { $arguments += "--api-only" }
    & $python @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
