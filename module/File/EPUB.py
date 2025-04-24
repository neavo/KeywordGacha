import os
import shutil
import zipfile

from bs4 import BeautifulSoup
from lxml import etree

from base.Base import Base
from module.Cache.CacheItem import CacheItem

class EPUB(Base):

    # 显式引用以避免打包问题
    etree

    # EPUB 文件中读取的标签范围
    EPUB_TAGS = ("p", "h1", "h2", "h3", "h4", "h5", "h6", "div", "li", "td")

    def __init__(self, config: dict) -> None:
        super().__init__()

        # 初始化
        self.config: dict = config
        self.input_path: str = config.get("input_folder")
        self.output_path: str = config.get("output_folder")
        self.source_language: str = config.get("source_language")
        self.target_language: str = config.get("target_language")

    # 在扩展名前插入文本
    def insert_target(self, path: str) -> str:
        root, ext = os.path.splitext(path)
        return f"{root}.{self.target_language.lower()}{ext}"

    # 在扩展名前插入文本
    def insert_source_target(self, path: str) -> str:
        root, ext = os.path.splitext(path)
        return f"{root}.{self.source_language.lower()}.{self.target_language.lower()}{ext}"

    # 读取
    def read_from_path(self, abs_paths: list[str]) -> list[CacheItem]:
        items:list[CacheItem] = []
        for abs_path in abs_paths:
            # 获取相对路径
            try:
                rel_path = os.path.relpath(abs_path, self.input_path)
            except Exception:
                rel_path = abs_path

            # 数据处理
            with zipfile.ZipFile(abs_path, "r") as zip_reader:
                for path in zip_reader.namelist():
                    if path.lower().endswith((".htm", ".html", ".xhtml")):
                        with zip_reader.open(path) as reader:
                            bs = BeautifulSoup(reader.read().decode("utf-8-sig"), "html.parser")
                            for dom in bs.find_all(EPUB.EPUB_TAGS):
                                # 跳过空标签或嵌套标签
                                if dom.get_text().strip() == "" or dom.find(EPUB.EPUB_TAGS) != None:
                                    continue

                                # 添加数据
                                items.append(CacheItem({
                                    "src": dom.get_text(),
                                    "dst": dom.get_text(),
                                    "tag": path,
                                    "row": len(items),
                                    "file_type": CacheItem.FileType.EPUB,
                                    "file_path": rel_path,
                                }))
                    elif path.lower().endswith(".ncx"):
                        with zip_reader.open(path) as reader:
                            bs = BeautifulSoup(reader.read().decode("utf-8-sig"), "lxml-xml")
                            for dom in bs.find_all("text"):
                                # 跳过空标签
                                if dom.get_text().strip() == "":
                                    continue

                                items.append(CacheItem({
                                    "src": dom.get_text(),
                                    "dst": dom.get_text(),
                                    "tag": path,
                                    "row": len(items),
                                    "file_type": CacheItem.FileType.EPUB,
                                    "file_path": rel_path,
                                }))

        return items