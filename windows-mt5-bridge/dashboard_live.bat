@echo off
chcp 65001 > nul
title Dashboard de Trading - Bridge V3

echo.
echo ================================
echo  DASHBOARD DE TRADING EN VIVO
echo ================================
echo.
echo Conectando a base de datos...
echo.

python dashboard_console.py

pause
