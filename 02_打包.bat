@echo off
@chcp 65001 > nul

    @REM 重置虚拟环境
    powershell -Command "Remove-Item -Path 'env' -Recurse -Force"
    powershell -Command "Remove-Item -Path 'dist' -Recurse -Force"

    @REM 部署虚拟环境
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.12.4/python-3.12.4-embed-amd64.zip -OutFile python.zip"
    powershell -Command "Expand-Archive -Path 'python.zip' -DestinationPath 'env'"
    powershell -Command "Remove-Item -Path 'python.zip' -Recurse -Force"
    powershell -Command "Invoke-WebRequest -Uri https://bootstrap.pypa.io/pip/get-pip.py -OutFile get-pip.py"
    powershell -Command ".\env\python.exe get-pip.py"
    powershell -Command "Remove-Item -Path 'get-pip.py' -Recurse -Force"
    powershell -Command "Copy-Item -Path 'resource\python312._pth' -Destination 'env\python312._pth' -Force"

    @REM 安装依赖
    powershell -Command ".\env\python.exe -m pip install -r requirements.txt"
    powershell -Command ".\env\python.exe -m pip cache purge"

    @REM 部署模型
    powershell -Command "Invoke-WebRequest -Uri https://github.com/neavo/KeywordGachaModel/releases/download/kg_ner_ja_onnx_cpu/kg_ner_ja_onnx_cpu.zip -OutFile onnx.zip"
    powershell -Command "Expand-Archive -Path 'onnx.zip' -DestinationPath 'dist\KeywordGacha\resource\kg_ner_ja_onnx_cpu'"
    powershell -Command "Remove-Item -Path 'onnx.zip' -Recurse -Force"    

    @REM 复制文件
    xcopy "env" "dist\KeywordGacha\env" /E /I /H /Y
    xcopy "model" "dist\KeywordGacha\model" /E /I /H /Y
    xcopy "helper" "dist\KeywordGacha\helper" /E /I /H /Y
    xcopy "prompt" "dist\KeywordGacha\prompt" /E /I /H /Y
    xcopy "resource\kg_ner_ja" "dist\KeywordGacha\resource\kg_ner_ja" /E /I /H /Y

    copy "01_启动.bat" "dist\KeywordGacha\"
    copy "main.py" "dist\KeywordGacha\"
    copy "config.json" "dist\KeywordGacha\"
    copy "blacklist.txt" "dist\KeywordGacha\"
    copy "resource\python312._pth" "dist\KeywordGacha\resource\"

pause