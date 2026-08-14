# simpleMD Desktop

Build on Windows 10/11 x64 with PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build_windows.ps1
```

Output: `dist\simpleMD.exe` with writable `data` and `workspace` directories beside it. The system WebView2 Runtime is required; the app must show its official install link when that runtime is unavailable.

Close simpleMD before rebuilding. The build now stages PyInstaller output in
`build\.simpleMD-build`, then replaces only the executable and `_internal`
runtime files. Existing `data` and `workspace` contents are preserved.

## Startup diagnostics

The packaged app writes one timestamped trace per launch under
`dist\data\startup-logs`. To profile repeated starts on Windows:

```powershell
.\scripts\profile_startup.ps1 -Runs 10
```

The profiler writes `startup-profile.csv` beside the executable and measures
time to the `frontend-mounted` event. Keep these traces when investigating a
future startup regression.

For reusable Python/pywebview/WebView2 startup guidance and the full
investigation record, see
[`docs/python-webview2-startup-troubleshooting.md`](../docs/python-webview2-startup-troubleshooting.md).
For a new web-app conversion, see the generalized
[`webapp-to-python-webview2-conversion-guide.md`](../docs/webapp-to-python-webview2-conversion-guide.md).

The startup stall was traced to pywebview recursively reflecting the bridge's
internal service objects (`SettingsStore`, `FileService`, `WorkspaceService`,
and the window) during JavaScript API injection. Marking those objects as
non-serializable reduces the reflected API from roughly 369 functions to the
15 intended bridge methods. Removing the duplicate splash meta-refresh is also
required so only one automatic navigation runs.

The final Windows profile reached `frontend-mounted` in 10/10 launches at
1.452–1.523 seconds (p95 1.523 seconds), with no timeouts. The preceding
single-navigation profile succeeded in 9/10 launches and ranged up to 7.843
seconds, while the file-URL experiment timed out in all 10 launches.
