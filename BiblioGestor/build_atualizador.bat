@echo off
chcp 65001 >nul
title Build do Atualizador BiblioGestor

echo.
echo  ============================================
echo     Build - Atualizar_BiblioGestor.exe
echo  ============================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERRO] Python nao encontrado.
    pause
    exit /b 1
)

pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo  [*] Instalando PyInstaller...
    pip install pyinstaller --quiet
)

echo  [*] Compilando atualizador...
echo.

pyinstaller --noconfirm --onefile --console ^
    --name "Atualizar_BiblioGestor" ^
    --clean ^
    "atualizador.py"

if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] Falha na compilacao.
    pause
    exit /b 1
)

echo.
echo  ============================================
echo     Build concluido!
echo  ============================================
echo.
echo  Executavel gerado em:
echo     %~dp0dist\Atualizar_BiblioGestor.exe
echo.
echo  Como distribuir:
echo    1. Envie o arquivo Atualizar_BiblioGestor.exe por WhatsApp/e-mail
echo    2. Ou coloque no pendrive junto com a pasta "pacote_atualizacao"
echo.
pause
