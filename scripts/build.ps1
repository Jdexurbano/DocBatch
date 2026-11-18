$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    throw 'Create .venv and install requirements.txt before building.'
}

$entry = Join-Path $root 'src\docbatch\__main__.py'
$source = Join-Path $root 'src'
& $python -m PyInstaller --noconfirm --clean --onedir --windowed --name DocBatch --paths $source $entry
if ($LASTEXITCODE -ne 0) {
    throw 'PyInstaller failed to build the DocBatch bundle.'
}

$iscc = Get-Command iscc -ErrorAction SilentlyContinue
if (-not $iscc) {
    Write-Host 'Bundle: dist\DocBatch'
    Write-Host 'Inno Setup 6 was not found on PATH; installer was not built.'
    exit 0
}

& $iscc.Source (Join-Path $root 'installer\DocBatch.iss')
if ($LASTEXITCODE -ne 0) {
    throw 'Inno Setup failed to build the installer.'
}

Write-Host 'Installer: dist\installer\DocBatch-1.0.0-setup.exe'
