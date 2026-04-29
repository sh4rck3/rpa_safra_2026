@echo off
REM Script para iniciar o servidor API RPA Safra

echo ========================================
echo   RPA SAFRA - API SERVER
echo ========================================
echo.

REM Verificar se o venv existe
if not exist "venv\" (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute primeiro: python -m venv venv
    echo.
    pause
    exit /b 1
)

REM Ativar ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Instalar/atualizar dependencias
echo.
echo Verificando dependencias...
pip install -r requirements.txt --quiet

REM Verificar se .env existe
if not exist ".env" (
    echo.
    echo [AVISO] Arquivo .env nao encontrado!
    echo Por favor, configure o arquivo .env antes de continuar.
    echo.
    pause
    exit /b 1
)

REM Iniciar servidor
echo.
echo ========================================
echo   INICIANDO SERVIDOR API
echo ========================================
echo.
echo Pressione Ctrl+C para parar
echo.

cd /d "%~dp0"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

pause
