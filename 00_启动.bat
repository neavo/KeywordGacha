@echo off
@chcp 65001 > nul

cd /d %~dp0
call env\python.exe main.py