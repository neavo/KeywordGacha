@echo off

	@REM 激活虚拟环境
	call conda activate KeywordGacha

	@REM 清理环境
	rd /s /q build
	del /q *.spec

	@REM 安装依赖
	pip install -r requirements.txt

	@REM 执行打包
	pyinstaller --distpath .\ --name KeywordGacha --clean --noconfirm --onefile main.py

	@REM 清理环境
	rd /s /q build
	del /q *.spec
	
	@REM 退出虚拟环境
	call conda deactivate

pause