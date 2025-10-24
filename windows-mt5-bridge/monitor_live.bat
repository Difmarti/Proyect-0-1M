@echo off
chcp 65001 > nul
title Monitor de Trading - Bridge V3

echo.
echo ================================
echo  MONITOR DE TRADING EN VIVO
echo ================================
echo.
echo Analizando: mt5_bridge_v3.log
echo Presiona Ctrl+C para detener
echo.

python monitor_trades.py

pause
