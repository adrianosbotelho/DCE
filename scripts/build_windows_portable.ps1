# Build portable dce.exe ZIP for Windows (run on Windows / CI only).
# Usage (PowerShell):
#   .\scripts\build_windows_portable.ps1
param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Version = & $Python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"
Write-Host "Building DCE $Version portable Windows zip..."

& $Python -m pip install -q -e ".[dev,portable]"

$Dist = Join-Path $Root "dist"
$Build = Join-Path $Root "build"
$PortableDir = Join-Path $Dist "dce-$Version-windows-x64"
$ZipPath = Join-Path $Dist "dce-$Version-windows-x64.zip"

if (Test-Path $PortableDir) { Remove-Item -Recurse -Force $PortableDir }
New-Item -ItemType Directory -Path $PortableDir | Out-Null

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --distpath (Join-Path $Build "pyinstaller-dist") `
  --workpath (Join-Path $Build "pyinstaller-work") `
  (Join-Path $Root "packaging\pyinstaller\dce.spec")

$Exe = Join-Path $Build "pyinstaller-dist\dce.exe"
if (-not (Test-Path $Exe)) {
    throw "PyInstaller did not produce dce.exe at $Exe"
}

Copy-Item $Exe (Join-Path $PortableDir "dce.exe")

$Readme = @"
DCE portable for Windows (x64)
Version: $Version

Quick start
-----------
1. Extract this ZIP anywhere (no installer).
2. Open PowerShell in this folder.
3. Smoke test:
     .\dce.exe --version
     .\dce.exe init C:\path\to\workspace
     .\dce.exe index C:\path\to\workspace

Kiro MCP (stdio)
----------------
Configure something like:

  command: C:\full\path\to\dce.exe
  args:    mcp --path C:\full\path\to\workspace

Notes
-----
- Windows Defender / SmartScreen may warn (unsigned binary).
- Prefer an absolute path to dce.exe in Kiro config.
- Offline after first extract; Jira REST still needs network + JIRA_* env if used.
"@
Set-Content -Path (Join-Path $PortableDir "README-WINDOWS.txt") -Value $Readme -Encoding UTF8

if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path (Join-Path $PortableDir "*") -DestinationPath $ZipPath -Force

$ShaPath = "$ZipPath.sha256"
$hash = (Get-FileHash -Path $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
$leaf = Split-Path $ZipPath -Leaf
Set-Content -Path $ShaPath -Value "$hash  $leaf" -Encoding ascii

Write-Host "OK: $ZipPath"
Write-Host "OK: $ShaPath ($hash)"
& $Exe --version
