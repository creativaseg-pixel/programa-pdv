@echo off
REM ============================================================
REM build_32.bat - Gera PDV_Supermercado_x86.exe (Windows 32-bit)
REM Requer: Python 3.9.13 (32 bits)
REM
REM AJUSTE O CAMINHO ABAIXO conforme onde voce instalou o Py 32-bit
REM Exemplos comuns:
REM   C:\Python39-32\python.exe
REM   C:\Users\SeuUser\AppData\Local\Programs\Python\Python39-32\python.exe
REM ============================================================
setlocal

echo.
echo ================================================
echo   Build 32-bit (Python 3.9.13)
echo ================================================
echo.

REM ===== AJUSTE ESTE CAMINHO =====
set PY32="C:\Python39-32\python.exe"

REM Tenta caminhos alternativos se o padrao nao existir
if not exist %PY32% set PY32="C:\Python39\python.exe"
if not exist %PY32% set PY32="%LocalAppData%\Programs\Python\Python39-32\python.exe"
if not exist %PY32% set PY32="%LocalAppData%\Programs\Python\Python39\python.exe"

if not exist %PY32% (
    echo ERRO: Nao encontrei o Python 3.9.13 32-bit
    echo Procurei em:
    echo   C:\Python39-32\python.exe
    echo   C:\Python39\python.exe
    echo   %%LocalAppData%%\Programs\Python\Python39-32\python.exe
    echo.
    echo Edite este arquivo .bat e ajuste a variavel PY32 com
    echo o caminho correto do seu Python 3.9.13 32-bit
    pause
    exit /b 1
)

echo Python encontrado em: %PY32%

echo.
echo Verificando arquitetura...
%PY32% -c "import struct; print('Arquitetura:', struct.calcsize('P') * 8, 'bits')"
%PY32% -c "import struct,sys; sys.exit(0 if struct.calcsize('P')==4 else 1)"
if errorlevel 1 (
    echo ERRO: Python neste caminho NAO eh 32-bit.
    pause
    exit /b 1
)

echo.
echo Limpando builds anteriores...
if exist "build" rmdir /S /Q "build"
if exist "dist\PDV_Supermercado.exe" del /Q "dist\PDV_Supermercado.exe"

echo.
echo Instalando dependencias (Python 32-bit)...
%PY32% -m pip install --quiet --upgrade pip
%PY32% -m pip install --quiet --upgrade pyinstaller pillow "qrcode[pil]"

echo.
echo Gerando executavel...
%PY32% -m PyInstaller pdv_supermercado.spec --clean --noconfirm
if errorlevel 1 (
    echo ERRO: Falha no PyInstaller
    pause
    exit /b 1
)

REM Renomeia para diferenciar arquitetura
if exist "dist\PDV_Supermercado.exe" (
    move /Y "dist\PDV_Supermercado.exe" "dist\PDV_Supermercado_x86.exe" >nul
    echo.
    echo ================================================
    echo   OK! Gerado: dist\PDV_Supermercado_x86.exe
    echo ================================================
) else (
    echo ERRO: Executavel nao foi gerado
    pause
    exit /b 1
)

endlocal
echo.
pause
