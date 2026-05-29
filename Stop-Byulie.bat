@echo off
title Stop Byulie
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_byulie.ps1"
pause
