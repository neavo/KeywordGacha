@echo off
@chcp 65001 > nul

    call env\scripts\activate
    call python main.py