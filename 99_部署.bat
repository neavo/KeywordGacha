@echo off
@chcp 65001 > nul

    @REM 设置工作目录
    cd /d %~dp0

    @REM 重置虚拟环境
    powershell -Command "Remove-Item -Path 'env' -Recurse -Force -ErrorAction SilentlyContinue"
    powershell -Command "Remove-Item -Path 'dist' -Recurse -Force -ErrorAction SilentlyContinue"

    @REM 部署虚拟环境
    .\resource\aria2c.exe https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip -o python.zip
    powershell -Command "Expand-Archive -Path 'python.zip' -DestinationPath 'env'"
    powershell -Command "Remove-Item -Path 'python.zip' -Recurse -Force -ErrorAction SilentlyContinue"

    .\resource\aria2c.exe https://bootstrap.pypa.io/pip/get-pip.py -o get-pip.py
    .\env\python.exe get-pip.py
    powershell -Command "Remove-Item -Path 'get-pip.py' -Recurse -Force -ErrorAction SilentlyContinue"
    powershell -Command "Copy-Item -Path 'resource\python312._pth' -Destination 'env\python312._pth' -Force"

    @REM 安装依赖
    .\env\python.exe -m pip install --upgrade pip
    .\env\python.exe -m pip install --upgrade setuptools
    .\env\python.exe -m pip install https://github.com/neavo/KeywordGachaModel/releases/download/kg_ner_20250131/triton-3.1.0.post9-cp312-cp312-win_amd64.whl
    .\env\python.exe -m pip install -r requirements.txt
    .\env\python.exe -m pip cache purge

    @REM 部署模型
    .\resource\aria2c.exe https://github.com/neavo/KeywordGachaModel/releases/download/kg_ner_20250131/kg_ner_bf16.zip -o kg_ner_bf16.zip
    powershell -Command "Expand-Archive -Path 'kg_ner_bf16.zip' -DestinationPath 'resource\kg_ner_bf16'"
    powershell -Command "Remove-Item -Path 'kg_ner_bf16.zip' -Recurse -Force -ErrorAction SilentlyContinue"

pause