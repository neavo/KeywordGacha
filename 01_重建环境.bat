@echo off
@chcp 65001 > nul

    @REM 重置虚拟环境
    rd /S /Q "env"
    rd /S /Q "dist"
    powershell -Command "Expand-Archive -Path 'resource\WinPython64.zip' -DestinationPath 'env'"

    @REM 激活虚拟环境
    call env\scripts\activate

    @REM 安装依赖
    call pip install --upgrade pip
    call pip install -r requirements.txt
    call python -m spacy download ja_core_news_lg

    @REM 打包步骤
    xcopy "env" "dist\KeywordGacha\env" /E /I /H /Y
    xcopy "model" "dist\KeywordGacha\model" /E /I /H /Y
    xcopy "helper" "dist\KeywordGacha\helper" /E /I /H /Y
    xcopy "prompt" "dist\KeywordGacha\prompt" /E /I /H /Y

    copy "00_启动.bat" "dist\KeywordGacha\"
    copy "main.py" "dist\KeywordGacha\"
    copy "config.json" "dist\KeywordGacha\"
    copy "blacklist.txt" "dist\KeywordGacha\"

pause