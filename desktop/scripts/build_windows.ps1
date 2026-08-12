param([switch]$VerifyOnly)

$ErrorActionPreference = "Stop"
$desktop = Split-Path $PSScriptRoot -Parent
Push-Location $desktop
try {
    if (-not $VerifyOnly) {
        npm --prefix client ci
        npm --prefix client run build
        $target = Join-Path $desktop "dist\Flatnotes"
        $stagingRoot = Join-Path $desktop "dist\.flatnotes-build"
        $staged = Join-Path $stagingRoot "Flatnotes"

        if (Get-Process -Name "Flatnotes" -ErrorAction SilentlyContinue) {
            throw "Flatnotes is running. Close it before rebuilding so packaged DLLs are not locked."
        }

        Remove-Item $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue
        uv run pyinstaller flatnotes_desktop.spec --noconfirm --clean --distpath $stagingRoot
        if (-not (Test-Path (Join-Path $staged "Flatnotes.exe"))) {
            throw "PyInstaller staging output missing: $staged"
        }

        New-Item -ItemType Directory -Force $target | Out-Null
        $targetInternal = Join-Path $target "_internal"
        if (Test-Path $targetInternal) {
            Remove-Item $targetInternal -Recurse -Force -ErrorAction Stop
        }
        Remove-Item (Join-Path $target "Flatnotes.exe") -Force -ErrorAction SilentlyContinue
        Copy-Item (Join-Path $staged "Flatnotes.exe") $target -Force
        Copy-Item (Join-Path $staged "_internal") $target -Recurse -Force
        New-Item -ItemType Directory -Force (Join-Path $target "data") | Out-Null
        Remove-Item $stagingRoot -Recurse -Force
    }
    $exe = Join-Path $desktop "dist\Flatnotes\Flatnotes.exe"
    if (-not (Test-Path $exe)) { throw "Flatnotes.exe missing" }
    if (-not (Test-Path (Join-Path (Split-Path $exe) "_internal"))) { throw "PyInstaller onedir support files missing" }
    if (-not (Test-Path (Join-Path (Split-Path $exe) "data"))) { throw "portable data directory missing" }
    Write-Host "Portable build verified: $exe"
    Write-Host "Distribute the entire dist\Flatnotes folder; Flatnotes.exe cannot run by itself."
} finally {
    Pop-Location
}
