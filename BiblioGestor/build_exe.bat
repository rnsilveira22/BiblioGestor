@echo off
chcp 65001 >nul
title BiblioGestor - Build

echo.
echo  ============================================
echo     Build do BiblioGestor - Executavel
echo  ============================================
echo.

cd /d "%~dp0"

REM ── Verifica Python ──
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERRO] Python nao encontrado. Execute instalar_e_abrir.bat primeiro.
    pause
    exit /b 1
)
echo  [OK] Python encontrado.

REM ── Instala PyInstaller se necessario ──
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo  [*] Instalando PyInstaller...
    pip install pyinstaller --quiet
)
echo  [OK] PyInstaller pronto.

REM ── Instala dependencias do projeto ──
echo  [*] Verificando dependencias...
pip install pandas openpyxl Pillow bcrypt --quiet
echo  [OK] Dependencias prontas.

REM ── Cria a pasta de saida ──
if not exist "dist" mkdir dist

REM ── Executa o PyInstaller ──
echo.
echo  [*] Compilando executavel (pode levar alguns minutos)...
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --name "BiblioGestor" ^
    --add-data "biblioteca.db;." ^
    --hidden-import "pandas" ^
    --hidden-import "openpyxl" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "bcrypt" ^
    --collect-submodules "PIL" ^
    "biblioteca.py"

if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] Falha na compilacao.
    pause
    exit /b 1
)

echo.
echo  ============================================
echo     Build concluido com sucesso!
echo  ============================================
echo.
echo  Executavel gerado em:
echo     %~dp0dist\BiblioGestor.exe
echo.
echo  Para executar, copie a pasta "dist" para qualquer
echo  computador Windows e execute o BiblioGestor.exe.
echo.

pause
