$ErrorActionPreference = 'Stop'

Set-Location $PSScriptRoot
& '.\.venv\Scripts\Activate.ps1'
python -m pip install -e .[dev]
Remove-Item -Recurse -Force '.\dist', '.\build' -ErrorAction SilentlyContinue
# Use the checked-in .spec as the single source of truth for PyInstaller configuration
pyinstaller --noconfirm --clean .\video-to-text.spec

