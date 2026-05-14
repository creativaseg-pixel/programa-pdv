@echo off
REM ============================================================
REM build_64.bat - Gera PDV_Supermercado_x64.exe (Windows 64-bit)
REM Requer: Python 3.12 (64 bits) no PATH
REM ============================================================
setlocal

echo.
echo ================================================
echo   Build 64-bit (Python 3.12)
echo ================================================
echo.

REM Verifica se Python esta acessivel
where python >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado no PATH.
    echo Instale Python 3.12 marcando "Add Python to PATH"
    pause
    exit /b 1
)

echo Verificando arquitetura...
python -c "import struct; print('Arquitetura:', struct.calcsize('P') * 8, 'bits')"
python -c "import struct,sys; sys.exit(0 if struct.calcsize('P')==8 else 1)"
if errorlevel 1 (
    echo ERRO: Python no PATH NAO eh 64-bit.
    echo Use o launcher py -3.12 ou ajuste o PATH.
    pause
    exit /b 1
)

echo.
echo Limpando builds anteriores...
if exist "build" rmdir /S /Q "build"
if exist "dist\PDV_Supermercado.exe" del /Q "dist\PDV_Supermercado.exe"

echo.
echo Instalando dependencias (Python 64-bit)...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet --upgrade pyinstaller pillow "qrcode[pil]"

echo.
echo Gerando executavel...
python -m PyInstaller pdv_supermercado.spec --clean --noconfirm
if errorlevel 1 (
    echo ERRO: Falha no PyInstaller
    pause
    exit /b 1
)

REM Renomeia para diferenciar arquitetura
if exist "dist\PDV_Supermercado.exe" (
    move /Y "dist\PDV_Supermercado.exe" "dist\PDV_Supermercado_x64.exe" >nul
    echo.
    echo ================================================
    echo   OK! Gerado: dist\PDV_Supermercado_x64.exe
    echo ================================================
) else (
    echo ERRO: Executavel nao foi gerado
    pause
    exit /b 1
)

endlocal
echo.
pause
