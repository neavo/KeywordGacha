@echo off
@chcp 65001 > nul

    call python -m venv env
    call env\Scripts\activate

    call python -m pip install --upgrade pip
    call pip install -r requirements.txt
    call python -m spacy download ja_core_news_lg

    @REM xcopy "env" "dist\KeywordGacha\env" /E /I /H /Y
    @REM xcopy "model" "dist\KeywordGacha\model" /E /I /H /Y
    @REM xcopy "helper" "dist\KeywordGacha\helper" /E /I /H /Y
    @REM xcopy "prompt" "dist\KeywordGacha\prompt" /E /I /H /Y

    @REM copy "00_启动.bat" "dist\KeywordGacha\"
    @REM copy "main.py" "dist\KeywordGacha\"
    @REM copy "config.json" "dist\KeywordGacha\"
    @REM copy "blacklist.txt" "dist\KeywordGacha\"

    call deactivate