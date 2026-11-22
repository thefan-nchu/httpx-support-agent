param(
    [ValidateSet('offline', 'evidence')]
    [string] $Mode = 'offline',
    [string] $Python = 'python',
    [int] $Port = 8767
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if ($Mode -eq 'evidence') { $env:SUPPORT_MODEL_MODE = '2' }
else { $env:SUPPORT_MODEL_MODE = '0' }
& $Python -B -m uvicorn app:app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
