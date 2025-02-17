import os
import sys
import PyInstaller.__main__

# 获取 pip 安装的 root 路径（site-packages）
def get_pip_root() -> str:
    return os.path.join(sys.prefix, "lib", "site-packages")

cmd = [
    "./app.py",
    "--clean", # Clean PyInstaller cache and remove temporary files before building
    "--onedir", # Create a one-folder bundle containing an executable (default)
    # "--onefile", # Create a one-file bundled executable
    "--noconfirm", # Replace output directory (default: SPECPATH/dist/SPECNAME) without asking for confirmation
    "--distpath=./dist", # Where to put the bundled app (default: ./dist)
    "--name=KeywordGacha"
]

if os.path.exists("./requirements.txt"):
    # 生成配置
    with open("./requirements.txt", "r", encoding = "utf-8") as reader:
        for line in reader:
            if not line.strip().startswith(("#", "--")):
                cmd.append("--hidden-import=" + line.strip())

            if line.strip() == "pykakasi":
                cmd.append(f"--add-data={get_pip_root()}/pykakasi:pykakasi")

    # 执行打包
    PyInstaller.__main__.run(cmd)

    # 更名
    if os.path.isfile("./dist/KeywordGacha/KeywordGacha.exe"):
        os.rename("./dist/KeywordGacha/KeywordGacha.exe", "./dist/KeywordGacha/app.exe")