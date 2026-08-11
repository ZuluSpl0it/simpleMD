param([switch]$VerifyOnly)

$ErrorActionPreference = "Stop"
$desktop = Split-Path $PSScriptRoot -Parent
Push-Location $desktop
try {
    if (-not $VerifyOnly) {
        npm --prefix client ci
        npm --prefix client run build
        uv run pyinstaller flatnotes_desktop.spec --noconfirm --clean
        New-Item -ItemType Directory -Force dist\Flatnotes | Out-Null
        Move-Item -Force dist\Flatnotes.exe dist\Flatnotes\Flatnotes.exe
        New-Item -ItemType Directory -Force dist\Flatnotes\data | Out-Null
    }
    $exe = Join-Path $desktop "dist\Flatnotes\Flatnotes.exe"
    if (-not (Test-Path $exe)) { throw "Flatnotes.exe missing" }
    if (-not (Test-Path (Join-Path (Split-Path $exe) "data"))) { throw "portable data directory missing" }
    Write-Host "Portable build verified: $exe"
} finally {
    Pop-Location
}
