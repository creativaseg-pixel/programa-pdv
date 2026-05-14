@echo off
REM ============================================================
REM build_all.bat - Script automatizado para gerar exe + instalador
REM Execute no PC Windows com Python e Inno Setup instalados
REM ============================================================

echo.
echo ================================================
echo   PDV Supermercado - Build Automatico
echo ================================================
echo.

REM 1. Limpa builds anteriores
echo [1/4] Limpando builds anteriores...
if exist "dist" rmdir /S /Q "dist"
if exist "build" rmdir /S /Q "build"
if exist "output" rmdir /S /Q "output"
echo OK.
echo.

REM 2. Instala/atualiza dependencias
echo [2/4] Instalando dependencias...
pip install --quiet --upgrade pyinstaller pillow qrcode[pil]
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias Python
    pause
    exit /b 1
)
echo OK.
echo.

REM 3. Gera o executavel
echo [3/4] Gerando PDV_Supermercado.exe ...
pyinstaller pdv_supermercado.spec --clean --noconfirm
if errorlevel 1 (
    echo ERRO: Falha ao gerar o executavel
    pause
    exit /b 1
)
echo OK. Executavel em: dist\PDV_Supermercado.exe
echo.

REM 4. Compila instalador com Inno Setup
echo [4/4] Compilando instalador Inno Setup...
REM Ajuste o caminho do ISCC.exe se necessario
set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_PATH% set INNO_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"

if not exist %INNO_PATH% (
    echo AVISO: Inno Setup nao encontrado. Instale em https://jrsoftware.org/isinfo.php
    echo O executavel foi gerado em dist\PDV_Supermercado.exe
    pause
    exit /b 0
)

%INNO_PATH% pdv_installer.iss
if errorlevel 1 (
    echo ERRO: Falha ao compilar instalador
    pause
    exit /b 1
)

echo.
echo ================================================
echo   BUILD CONCLUIDO COM SUCESSO!
echo ================================================
echo.
echo Executavel:  dist\PDV_Supermercado.exe
echo Instalador:  output\setup_PDV_Supermercado_v1.0.0.exe
echo.
pause
