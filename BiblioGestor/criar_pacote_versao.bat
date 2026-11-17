@echo off
chcp 65001 >nul
title BiblioGestor - Criar Pacote de Versão

echo.
echo  ============================================
echo     Criar Pacote de Versão do BiblioGestor
echo  ============================================
echo.

cd /d "%~dp0"

set /p VERSAO="  Digite o número da versão (ex: 1.1.0): "
if "%VERSAO%"=="" (
    echo  [ERRO] Versão não informada.
    pause
    exit /b 1
)

echo %VERSAO%> versao.txt
echo  [OK] versao.txt = %VERSAO%

REM Atualiza VERSAO dentro de biblioteca.py (se existir)
if exist biblioteca.py (
    powershell -Command "(Get-Content biblioteca.py -Raw) -replace 'VERSAO\s*=\s*\"[^\"]+\"', 'VERSAO = \"%VERSAO%\"' | Set-Content biblioteca.py -NoNewline"
    echo  [OK] VERSAO atualizada em biblioteca.py
)

set "PACOTE=pacote_v%VERSAO%"
if exist "%PACOTE%" rmdir /s /q "%PACOTE%"
mkdir "%PACOTE%"

echo.
echo  [*] Copiando arquivos do sistema para o pacote...

for %%F in (
    biblioteca.py
    config.py
    importar_livros.py
    requirements.txt
    versao.txt
    BiblioGestor.bat
    instalar_e_abrir.bat
    atualizador.py
    Atualizar_BiblioGestor.bat
    COMO_ATUALIZAR.txt
) do (
    if exist "%%F" (
        copy /y "%%F" "%PACOTE%\%%F" >nul
        echo      + %%F
    )
)

if exist tests (
    xcopy /e /i /y tests "%PACOTE%\tests" >nul
    echo      + tests\
)

echo.
echo  [*] Gerando ZIP do pacote...
powershell -Command "Compress-Archive -Path '%PACOTE%\*' -DestinationPath 'BiblioGestor_v%VERSAO%.zip' -Force"
if exist "BiblioGestor_v%VERSAO%.zip" (
    echo  [OK] Pacote criado: BiblioGestor_v%VERSAO%.zip
) else (
    echo  [!] ZIP não foi gerado. A pasta %PACOTE% ainda pode ser usada.
)

echo.
echo  ============================================
echo     Pacote pronto!
echo  ============================================
echo.
echo  Arquivos gerados:
echo    - pasta:  %PACOTE%\
echo    - zip:    BiblioGestor_v%VERSAO%.zip
echo.
echo  Como distribuir:
echo    1. Envie o ZIP + Atualizar_BiblioGestor.exe ao cliente
echo    2. Ou coloque no pendrive:
echo         Atualizar_BiblioGestor.exe
echo         pacote_atualizacao\   ^(conteúdo de %PACOTE%^)
echo.
pause
