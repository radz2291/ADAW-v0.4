param([Parameter(Mandatory=$true)][string]$PythonExe)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$version = & $PythonExe -c 'import sys,platform; print(platform.python_version()+" "+platform.machine())'
if ($LASTEXITCODE -ne 0 -or $version -ne '3.12.14 AMD64') { throw 'Use native Windows x64 CPython 3.12.14 (the tested baseline).' }
& $PythonExe -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'venv creation failed' }
& .\.venv\Scripts\python.exe -m pip install --require-hashes --only-binary=:all: -r requirements.lock
if ($LASTEXITCODE -ne 0) { throw 'Locked install failed' }
& .\.venv\Scripts\python.exe -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed' }

