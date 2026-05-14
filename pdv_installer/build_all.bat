@echo off
REM ============================================================
REM build_all.bat - Gera os DOIS executaveis (32 e 64 bits)
REM e compila o instalador unico (detecta arquitetura no install)
REM
REM Requisitos no PC:
REM   - Python 3.12 (64 bits) no PATH
REM   - Python 3.9.13 (32 bits) em C:\Python39-32\ (ajuste no build_32.bat)
REM   - Inno Setup 6 instalado
REM ============================================================
setlocal

echo.
echo ================================================================
echo   PDV Supermercado - BUILD COMPLETO (32 + 64 bits)
echo ================================================================
echo.

REM Build 64-bit
call build_64.bat
if errorlevel 1 (
    echo Falha no build 64-bit. Abortando.
    exit /b 1
)

echo.
REM Build 32-bit
call build_32.bat
if errorlevel 1 (
    echo Falha no build 32-bit. Abortando.
    exit /b 1
)

REM Verifica se os dois exes foram gerados
if not exist "dist\PDV_Supermercado_x64.exe" (
    echo ERRO: dist\PDV_Supermercado_x64.exe nao encontrado.
    pause
    exit /b 1
)
if not exist "dist\PDV_Supermercado_x86.exe" (
    echo ERRO: dist\PDV_Supermercado_x86.exe nao encontrado.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Compilando instalador unico (Inno Setup)
echo ================================================
echo.

REM Localiza ISCC.exe (compilador do Inno Setup)
set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_PATH% set INNO_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
if not exist %INNO_PATH% set INNO_PATH="C:\Program Files (x86)\Inno Setup 5\ISCC.exe"

if not exist %INNO_PATH% (
    echo AVISO: Inno Setup nao encontrado.
    echo Baixe em: https://jrsoftware.org/isinfo.php
    echo Os executaveis foram gerados em dist\, mas o instalador nao.
    pause
    exit /b 0
)

%INNO_PATH% pdv_installer.iss
if errorlevel 1 (
    echo ERRO: Falha ao compilar o instalador
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   BUILD CONCLUIDO!
echo ================================================================
echo.
echo Executaveis (standalone, sem dependencias):
echo   dist\PDV_Supermercado_x64.exe  (Windows 64 bits)
echo   dist\PDV_Supermercado_x86.exe  (Windows 32 bits)
echo.
echo Instalador profissional unico (detecta arquitetura):
echo   output\setup_PDV_Supermercado_v1.0.0.exe
echo.
endlocal
pause
