@echo off
title Byulie Launcher
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_byulie.ps1"
if errorlevel 1 pause
