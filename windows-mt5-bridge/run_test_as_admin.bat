@echo off
cd /d "%~dp0"
echo Ejecutando test de MT5 con privilegios de administrador...
echo Directorio actual: %CD%
echo.
python test_mt5_only.py
echo.
pause
