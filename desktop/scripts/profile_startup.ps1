param(
    [int]$Runs = 10,
    [int]$TimeoutSeconds = 45
)

$ErrorActionPreference = "Stop"
$desktop = Split-Path $PSScriptRoot -Parent
$exe = Join-Path $desktop "dist\Flatnotes\Flatnotes.exe"
$logDirectory = Join-Path $desktop "dist\Flatnotes\data\startup-logs"
$results = @()

if (-not (Test-Path $exe)) { throw "Flatnotes.exe missing: $exe" }
New-Item -ItemType Directory -Force $logDirectory | Out-Null

for ($run = 1; $run -le $Runs; $run++) {
    $started = Get-Date
    $process = Start-Process -FilePath $exe -PassThru
    $deadline = $started.AddSeconds($TimeoutSeconds)
    $trace = $null
    $mountedSeconds = $null

    try {
        while ((Get-Date) -lt $deadline) {
            $trace = Get-ChildItem $logDirectory -Filter "*-$($process.Id).log" |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1

            if ($trace) {
                $match = Select-String -Path $trace.FullName -Pattern '^\+([0-9.]+)s .* frontend-mounted$' |
                    Select-Object -Last 1
                if ($match) {
                    $mountedSeconds = [double]$match.Matches[0].Groups[1].Value
                    break
                }
            }
            Start-Sleep -Milliseconds 100
        }
    } finally {
        if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force }
    }

    $results += [pscustomobject]@{
        Run = $run
        FrontendMountedSeconds = $mountedSeconds
        TimedOut = ($null -eq $mountedSeconds)
        Trace = if ($trace) { $trace.FullName } else { "" }
    }
}

$csv = Join-Path $desktop "startup-profile.csv"
$results | Export-Csv -Path $csv -NoTypeInformation
$results | Format-Table -AutoSize

$successful = @($results | Where-Object { -not $_.TimedOut } | Sort-Object FrontendMountedSeconds)
if ($successful.Count -gt 0) {
    $p95Index = [Math]::Ceiling($successful.Count * 0.95) - 1
    $p95 = $successful[$p95Index].FrontendMountedSeconds
    Write-Host "Successful: $($successful.Count)/$Runs; p95: $p95 seconds"
}
Write-Host "CSV: $csv"
