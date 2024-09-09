@echo off
@chcp 65001 > nul

    @REM 设置工作目录
    cd /d %~dp0

    @REM 重置虚拟环境
    powershell -Command "Remove-Item -Path 'env' -Recurse -Force -ErrorAction SilentlyContinue"
    powershell -Command "Remove-Item -Path 'dist' -Recurse -Force -ErrorAction SilentlyContinue"

    @REM 部署虚拟环境
    .\resource\aria2c.exe https://www.python.org/ftp/python/3.12.6/python-3.12.6-embed-amd64.zip -o python.zip
    powershell -Command "Expand-Archive -Path 'python.zip' -DestinationPath 'env'"
    powershell -Command "Remove-Item -Path 'python.zip' -Recurse -Force -ErrorAction SilentlyContinue"

    .\resource\aria2c.exe https://bootstrap.pypa.io/pip/get-pip.py -o get-pip.py
    .\env\python.exe get-pip.py
    powershell -Command "Remove-Item -Path 'get-pip.py' -Recurse -Force -ErrorAction SilentlyContinue"
    powershell -Command "Copy-Item -Path 'resource\python312._pth' -Destination 'env\python312._pth' -Force"

    @REM 安装依赖
    .\env\python.exe -m pip install --upgrade pip
    .\env\python.exe -m pip install --upgrade setuptools
    .\env\python.exe -m pip install -r requirements.txt
    .\env\python.exe -m pip cache purge

    @REM 部署模型
    .\resource\aria2c.exe https://github.com/neavo/KeywordGachaModel/releases/download/kg_ner_20240826/kg_ner_cpu.zip -o kg_ner_cpu.zip
    powershell -Command "Expand-Archive -Path 'kg_ner_cpu.zip' -DestinationPath 'dist\KeywordGacha\resource\kg_ner_cpu'"
    powershell -Command "Remove-Item -Path 'kg_ner_cpu.zip' -Recurse -Force -ErrorAction SilentlyContinue"

    @REM 复制文件
    xcopy "env" ".\dist\KeywordGacha\env" /E /I /Q /H /Y
    xcopy "model" ".\dist\KeywordGacha\model" /E /I /Q /H /Y
    xcopy "helper" ".\dist\KeywordGacha\helper" /E /I /Q /H /Y
    xcopy "prompt" ".\dist\KeywordGacha\prompt" /E /I /Q /H /Y

    copy "01_启动.bat" ".\dist\KeywordGacha\"
    copy "main.py" ".\dist\KeywordGacha\"
    copy "config.json" ".\dist\KeywordGacha\"
    copy "version.txt" ".\dist\KeywordGacha\"
    copy "blacklist.txt" ".\dist\KeywordGacha\"
    copy "libomp140.x86_64.dll" ".\dist\KeywordGacha\"

pause