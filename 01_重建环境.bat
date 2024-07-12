@echo off
@chcp 65001 > nul

    call conda create --name KeywordGacha python=3.12 --yes
    call conda activate KeywordGacha

    call pip install -r requirements.txt
    call python -m spacy download ja_core_news_lg

    rd /s /q dist
    rd /s /q envs
    xcopy "%USERPROFILE%\miniconda3\envs\KeywordGacha" "envs" /E /I /H /Y

    @REM xcopy "envs" "dist\KeywordGacha\envs" /E /I /H /Y
    @REM xcopy "model" "dist\KeywordGacha\model" /E /I /H /Y
    @REM xcopy "helper" "dist\KeywordGacha\helper" /E /I /H /Y
    @REM xcopy "prompt" "dist\KeywordGacha\prompt" /E /I /H /Y

    @REM copy /y "00_启动.bat" "dist\KeywordGacha\"
    @REM copy /y "main.py" "dist\KeywordGacha\"
    @REM copy /y "config.json" "dist\KeywordGacha\"
    @REM copy /y "blacklist.txt" "dist\KeywordGacha\"

    call conda deactivate
    call conda env remove --name KeywordGacha --yes