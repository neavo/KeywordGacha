@echo off
@chcp 65001 > nul

@REM 设置工作目录
cd /d %~dp0

@REM 打印信息
set "message1=　应用内 GPU 加速可以在 NER 实体识别环节提升 5 - 10 倍的速度。"
set "message2=　启用前请注意："
set "message3=　　1、仅支持 NVIDIA 显卡，并确保安装了最新版本的驱动程序；"
set "message4=　　2、如果要同时使用 本地接口 和 应用内 GPU 加速，则至少需要 10G 显存；"
set "message5=　　3、安装过程将从网络下载大约 3G-5G 的数据文件，请确保网络和代理通畅，保持耐心；"

echo.
echo =====================================================================================
echo ==
echo ==%message1%
echo ==%message2%
echo ==
echo ==%message3%
echo ==%message4%
echo ==%message5%
echo ==
echo =====================================================================================

@REM 等待用户输入
echo.
echo 是否确认启用 (Y/N)：

@REM 读取用户的输入前清空response变量
set "response="

@REM 读取用户的输入
set /p "response="

@REM 根据用户的输入做出响应
if /i "%response%"=="Y" goto P_INSTALL
if /i "%response%"=="y" goto P_INSTALL

@REM 如果用户没有输入任何内容，则取消安装
if /i "%response%"=="" (
    echo.
    echo 安装已取消 ...
    goto P_END
)

@REM 如果以上都不匹配，则取消安装
echo.
echo 安装已取消 ...
goto P_END

@REM 安装步骤
:P_INSTALL
    echo.
    echo 开始安装 ...

    @REM 更换 Torch 版本
    call env\python.exe -m pip uninstall --yes torch torchvision torchaudio
    call env\python.exe -m pip install torch torchvision torchaudio --index-url https://mirror.sjtu.edu.cn/pytorch-wheels/cu124
    
    @REM 下载 GPU 模型并解压
    call resource\aria2c.exe https://github.com/neavo/KeywordGachaModel/releases/download/kg_ner_ja_gpu/kg_ner_ja_gpu.zip -o kg_ner_ja_gpu.zip
    powershell -Command "Remove-Item -Path 'resource\kg_ner_ja_gpu' -Recurse -Force -ErrorAction SilentlyContinue"
    powershell -Command "Expand-Archive -Path 'kg_ner_ja_gpu.zip' -DestinationPath 'resource\kg_ner_ja_gpu'"
    powershell -Command "Remove-Item -Path 'kg_ner_ja_gpu.zip' -Recurse -Force -ErrorAction SilentlyContinue"

    @REM 生成标志文件
    echo > gpuboost.txt
    echo 已启用应用内 GPU 加速 ...

@REM 结束脚本
:P_END
    echo.
    pause