@echo off
@chcp 65001 > nul

    @REM 设置工作目录
    cd /d %~dp0

    @REM 重置虚拟环境
    powershell -Command "Remove-Item -Path 'env' -Recurse -Force -ErrorAction SilentlyContinue"
    powershell -Command "Remove-Item -Path 'dist' -Recurse -Force -ErrorAction SilentlyContinue"

    @REM 部署虚拟环境
    .\resource\aria2c.exe https://www.python.org/ftp/python/3.12.4/python-3.12.4-embed-amd64.zip -o python.zip
    powershell -Command "Expand-Archive -Path 'python.zip' -DestinationPath 'env'"
    powershell -Command "Remove-Item -Path 'python.zip' -Recurse -Force -ErrorAction SilentlyContinue"

    .\resource\aria2c.exe https://bootstrap.pypa.io/pip/get-pip.py -o get-pip.py
    .\env\python.exe get-pip.py
    powershell -Command "Remove-Item -Path 'get-pip.py' -Recurse -Force -ErrorAction SilentlyContinue"
    powershell -Command "Copy-Item -Path 'resource\python312._pth' -Destination 'env\python312._pth' -Force"

    @REM 安装依赖
    .\env\python.exe -m pip install -r requirements.txt
    .\env\python.exe -m pip cache purge

    @REM 部署模型
    .\resource\aria2c.exe https://github.com/neavo/KeywordGachaModel/releases/download/kg_ner_ja_cpu/kg_ner_ja_cpu.zip -o kg_ner_ja_cpu.zip
    powershell -Command "Expand-Archive -Path 'kg_ner_ja_cpu.zip' -DestinationPath 'dist\KeywordGacha\resource\kg_ner_ja_cpu'"
    powershell -Command "Remove-Item -Path 'kg_ner_ja_cpu.zip' -Recurse -Force -ErrorAction SilentlyContinue"    

    @REM 复制文件
    xcopy "env" ".\dist\KeywordGacha\env" /E /I /Q /H /Y
    xcopy "model" ".\dist\KeywordGacha\model" /E /I /Q /H /Y
    xcopy "helper" ".\dist\KeywordGacha\helper" /E /I /Q /H /Y
    xcopy "prompt" ".\dist\KeywordGacha\prompt" /E /I /Q /H /Y

    copy "01_启动.bat" ".\dist\KeywordGacha\"
    copy "main.py" ".\dist\KeywordGacha\"
    copy "config.json" ".\dist\KeywordGacha\"
    copy "blacklist.txt" ".\dist\KeywordGacha\"
    copy "libomp140.x86_64.dll" ".\dist\KeywordGacha\"

    @REM 压缩dist目录下的所有文件，不包括dist目录本身
    .\resource\7za.exe a -y -bt -mx5 -slp KeywordGacha.zip .\dist\*

    @REM 切换 Torch 版本
    .\dist\KeywordGacha\env\python.exe -m pip uninstall --yes torch torchvision torchaudio
    .\dist\KeywordGacha\env\python.exe -m pip install D:\AI\torch-2.3.1+cu121-cp312-cp312-win_amd64.whl
    .\dist\KeywordGacha\env\python.exe -m pip cache purge

    .\resource\aria2c.exe https://github.com/neavo/KeywordGachaModel/releases/download/kg_ner_ja_gpu/kg_ner_ja_gpu.zip -o kg_ner_ja_gpu.zip
    powershell -Command "Expand-Archive -Path 'kg_ner_ja_gpu.zip' -DestinationPath 'dist\KeywordGacha\resource\kg_ner_ja_gpu'"
    powershell -Command "Remove-Item -Path 'kg_ner_ja_gpu.zip' -Recurse -Force -ErrorAction SilentlyContinue"
    echo > .\dist\KeywordGacha\gpuboost.txt

    @REM  压缩dist目录下的所有文件，不包括dist目录本身
    .\resource\7za.exe a -y -bt -mx5 -slp -v2000M KeywordGacha_NV.zip .\dist\*

pause