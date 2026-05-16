@echo off
chcp 65001 >nul
title BiblioGestor - Instalador

echo.
echo  ============================================
echo     BiblioGestor - Instalacao e Execucao
echo  ============================================
echo.

set "SCRIPT_DIR=%~dp0"

REM ── Verifica se ja existe executavel compilado ──
if exist "%SCRIPT_DIR%dist\BiblioGestor.exe" (
    echo  [OK] Executavel encontrado. Iniciando...
    start "" "%SCRIPT_DIR%dist\BiblioGestor.exe"
    exit /b 0
)

REM ── Verifica Python ──
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] Python nao encontrado. Baixando instalador...
    echo.

    REM Baixa o instalador do Python 3.12
    curl -L -o "%TEMP%\python_installer.exe" "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"

    echo  [*] Instalando Python (pode demorar alguns minutos)...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_tcltk=1

    REM Atualiza PATH para esta sessao
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"

    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo  [ERRO] Falha na instalacao do Python.
        echo  Por favor, instale manualmente em: https://www.python.org/downloads/
        echo  Marque a opcao "Add Python to PATH" durante a instalacao.
        pause
        exit /b 1
    )
    echo  [OK] Python instalado com sucesso!
) else (
    echo  [OK] Python encontrado.
)

REM ── Instala dependencias ──
echo.
echo  [*] Verificando dependencias...

pip install pandas openpyxl Pillow --quiet
echo  [OK] Dependencias instaladas.

REM ── Cria atalho na Area de Trabalho ──
echo.
echo  [*] Criando atalho na Area de Trabalho...

powershell -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\BiblioGestor.lnk'); ^
   $s.TargetPath = 'pythonw.exe'; ^
   $s.Arguments = '\"%SCRIPT_DIR%biblioteca.py\"'; ^
   $s.WorkingDirectory = '%SCRIPT_DIR%'; ^
   $s.Description = 'BiblioGestor - Sistema de Biblioteca'; ^
   $s.Save()" >nul 2>&1

if exist "%USERPROFILE%\Desktop\BiblioGestor.lnk" (
    echo  [OK] Atalho criado na Area de Trabalho!
) else (
    echo  [AVISO] Nao foi possivel criar o atalho automaticamente.
)

REM ── Inicia o sistema ──
echo.
echo  [*] Iniciando BiblioGestor...
echo.
start "" pythonw "%SCRIPT_DIR%biblioteca.py"

echo  [OK] Sistema iniciado! Pode fechar esta janela.
echo.
timeout /t 3 >nul
