@echo off
chcp 65001 >nul
title BiblioGestor - Atualizador

cd /d "%~dp0"

REM Preferência: se existir o .exe, usa ele
if exist "%~dp0Atualizar_BiblioGestor.exe" (
    start "" "%~dp0Atualizar_BiblioGestor.exe"
    exit /b 0
)

REM Senão, tenta Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python "%~dp0atualizador.py"
    exit /b 0
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    python3 "%~dp0atualizador.py"
    exit /b 0
)

echo.
echo  [ERRO] Nem o executavel nem o Python foram encontrados.
echo.
echo  Opcoes:
echo    1. Coloque o arquivo Atualizar_BiblioGestor.exe nesta pasta
echo    2. Ou instale o Python e execute novamente
echo.
pause
