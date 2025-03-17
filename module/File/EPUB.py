import zipfile

from bs4 import BeautifulSoup
from lxml import etree

class EPUB():

    # 显式引用以避免打包问题
    etree

    # EPUB 文件中读取的标签范围
    EPUB_TAGS = ("p", "h1", "h2", "h3", "h4", "h5", "h6", "div", "li", "td")

    def __init__(self) -> None:
        super().__init__()

    # 读取
    def read_from_path(self, abs_paths: list[str]) -> list[str]:
        items: list[str] = []
        for abs_path in set(abs_paths):
            # 数据处理
            with zipfile.ZipFile(abs_path, "r") as zip_reader:
                for path in zip_reader.namelist():
                    if path.lower().endswith((".html", ".xhtml")):
                        with zip_reader.open(path) as reader:
                            bs = BeautifulSoup(reader.read().decode("utf-8-sig"), "html.parser")
                            for dom in bs.find_all(EPUB.EPUB_TAGS):
                                # 跳过空标签或嵌套标签
                                if dom.get_text().strip() == "" or dom.find(EPUB.EPUB_TAGS) != None:
                                    continue

                                # 添加数据
                                items.append(dom.get_text())
                    elif path.lower().endswith(".ncx"):
                        with zip_reader.open(path) as reader:
                            bs = BeautifulSoup(reader.read().decode("utf-8-sig"), "lxml-xml")
                            for dom in bs.find_all("text"):
                                # 跳过空标签
                                if dom.get_text().strip() == "":
                                    continue

                                 # 添加数据
                                items.append(dom.get_text())

        return items