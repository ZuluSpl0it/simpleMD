# Flatnotes Desktop

Build on Windows 10/11 x64 with PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build_windows.ps1
```

Output: `dist\Flatnotes\Flatnotes.exe` with a writable `data` directory beside it. The system WebView2 Runtime is required; the app must show its official install link when that runtime is unavailable.
