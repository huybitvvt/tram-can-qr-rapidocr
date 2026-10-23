$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$iscc = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
if (-not (Test-Path -LiteralPath $iscc)) {
    $iscc = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'
}
if (-not (Test-Path -LiteralPath $iscc)) { throw 'Can Inno Setup 6 de tao bo cai' }
& $python -c "import PyInstaller; assert PyInstaller.__version__ == '6.21.0'"
if ($LASTEXITCODE -ne 0) { throw 'Install requirements-build.txt first' }
& $python -m pytest
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
# PowerShell 5 can report ordinary native stderr progress as an error when
# the caller redirects the build log. Preserve the real tool exit code.
$previousErrorPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    & $python -m PyInstaller --noconfirm --clean packaging\TramCanOCRTrial.spec 2>&1 |
        ForEach-Object { Write-Output $_.ToString() }
    $pyInstallerExit = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $previousErrorPreference
}
if ($pyInstallerExit -ne 0) { throw "PyInstaller failed (exit $pyInstallerExit)" }
& $iscc packaging\TramCanOCRTrial.iss
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed' }
$installer = Join-Path $projectRoot 'dist\installer\TramCanOCRTrial-Setup-0.2.0-trial1.exe'
$hash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
($hash + '  ' + [IO.Path]::GetFileName($installer)) |
    Set-Content -LiteralPath 'dist\installer\SHA256SUMS.txt' -Encoding ascii
Copy-Item -LiteralPath 'docs\CAI-BAN-THU.md' -Destination 'dist\installer\CAI-BAN-THU.md' -Force
Write-Output $installer
