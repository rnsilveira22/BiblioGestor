@echo off
cd /d "%~dp0"
if exist "dist\BiblioGestor.exe" (
    start "" "dist\BiblioGestor.exe"
) else (
    start "" pythonw biblioteca.py
)
