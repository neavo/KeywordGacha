@echo off
@chcp 65001 > nul

    call conda create --name KeywordGacha python=3.12 --yes
    call conda activate KeywordGacha

    call python -m pip install --upgrade pip
    call pip install -r requirements.txt
    call python -m spacy download ja_core_news_lg

    rd /S /Q dist
    rd /S /Q envs

    @REM Github Action 路径
    @REM xcopy "C:\Miniconda\envs\KeywordGacha" "envs" /E /I /H /Y

    @REM 本机路径
    xcopy "%USERPROFILE%\miniconda3\envs\KeywordGacha" "envs" /E /I /H /Y

    @REM xcopy "envs" "dist\KeywordGacha\envs" /E /I /H /Y
    @REM xcopy "model" "dist\KeywordGacha\model" /E /I /H /Y
    @REM xcopy "helper" "dist\KeywordGacha\helper" /E /I /H /Y
    @REM xcopy "prompt" "dist\KeywordGacha\prompt" /E /I /H /Y

    @REM copy "00_启动.bat" "dist\KeywordGacha\"
    @REM copy "main.py" "dist\KeywordGacha\"
    @REM copy "config.json" "dist\KeywordGacha\"
    @REM copy "blacklist.txt" "dist\KeywordGacha\"

    call conda deactivate
    call conda env remove --name KeywordGacha --yes