$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$virtualEnvironmentPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"

Set-Location $repositoryRoot
if (Test-Path -LiteralPath $virtualEnvironmentPython) {
    $pythonCommand = $virtualEnvironmentPython
} else {
    $pythonCommand = (Get-Command python -ErrorAction Stop).Source
}

& $pythonCommand -m vortenix_newsletter.cli.app workflow run-scheduled --audience anish_daily
exit $LASTEXITCODE
