@echo off
@chcp 65001 > nul

@REM 设置工作目录
cd /d %~dp0

@REM 移除标志文件
powershell -Command "Remove-Item -Path 'gpuboost.txt' -Recurse -Force -ErrorAction SilentlyContinue"
echo 已关闭应用内 GPU 加速 ...

@REM 结束脚本
:P_END
    echo.
    pause