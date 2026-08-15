param([switch]$VerifyOnly)

$ErrorActionPreference = "Stop"
$desktop = Split-Path $PSScriptRoot -Parent
Push-Location $desktop
try {
    if (-not $VerifyOnly) {
        npm --prefix client ci
        npm --prefix client run build
        $target = Join-Path $desktop "dist"
        $stagingRoot = Join-Path $desktop "build\.simpleMD-build"
        $staged = Join-Path $stagingRoot "simpleMD"

        if ((Get-Process -Name "simpleMD" -ErrorAction SilentlyContinue) -or
            (Get-Process -Name "simpleMD" -ErrorAction SilentlyContinue)) {
            throw "simpleMD is running. Close it before rebuilding so packaged DLLs are not locked."
        }

        Remove-Item $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue
        uv run pyinstaller flatnotes_desktop.spec --noconfirm --clean --distpath $stagingRoot
        if (-not (Test-Path (Join-Path $staged "simpleMD.exe"))) {
            throw "PyInstaller staging output missing: $staged"
        }

        New-Item -ItemType Directory -Force $target | Out-Null
        $targetInternal = Join-Path $target "_internal"
        if (Test-Path $targetInternal) {
            Remove-Item $targetInternal -Recurse -Force -ErrorAction Stop
        }
        Remove-Item (Join-Path $target "simpleMD.exe") -Force -ErrorAction SilentlyContinue
        Remove-Item (Join-Path $target "Flatnotes.exe") -Force -ErrorAction SilentlyContinue
        Copy-Item (Join-Path $staged "simpleMD.exe") $target -Force
        Copy-Item (Join-Path $staged "_internal") $target -Recurse -Force
        New-Item -ItemType Directory -Force (Join-Path $target "data") | Out-Null

        # Give the portable distribution folder the same icon as the app. The
        # relative executable reference keeps this working after the folder is
        # moved to another drive or machine.
        $folderIconConfig = Join-Path $target "desktop.ini"
        @"
[.ShellClassInfo]
IconResource=simpleMD.exe,0
"@ | Set-Content -Path $folderIconConfig -Encoding Unicode
        attrib +s $target
        attrib +h +s $folderIconConfig

        Remove-Item $stagingRoot -Recurse -Force
    }
    $exe = Join-Path $desktop "dist\simpleMD.exe"
    if (-not (Test-Path $exe)) { throw "simpleMD.exe missing" }
    if (-not (Test-Path (Join-Path (Split-Path $exe) "_internal"))) { throw "PyInstaller onedir support files missing" }
    if (-not (Test-Path (Join-Path (Split-Path $exe) "data"))) { throw "portable data directory missing" }
    Write-Host "Portable build verified: $exe"
    Write-Host "Distribute the entire dist folder; simpleMD.exe cannot run by itself."
} finally {
    Pop-Location
}
