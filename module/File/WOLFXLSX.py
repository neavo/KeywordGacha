import os
import shutil

import openpyxl
import openpyxl.styles
import openpyxl.worksheet.worksheet

from base.Base import Base
from module.Cache.CacheItem import CacheItem

class WOLFXLSX(Base):

    BLACKLIST_EXT: tuple[str] = (
        ".mp3", ".wav", ".ogg", "mid",
        ".png", ".jpg", ".jpeg", ".gif", ".psd", ".webp", ".heif", ".heic",
        ".avi", ".mp4", ".webm",
        ".txt", ".7z", ".gz", ".rar", ".zip", ".json",
        ".sav", ".mps", ".ttf", ".otf", ".woff",
    )

    FILL_COLOR_WHITELIST: tuple = (
        9,                                                              # 白色
    )

    FILL_COLOR_BLACKLIST: tuple = (
        44,                                                             # 蓝色
        47,                                                             # 土黄
        55,                                                             # 灰色
    )

    def __init__(self, config: dict) -> None:
        super().__init__()

        # 初始化
        self.config: dict = config
        self.input_path: str = config.get("input_folder")
        self.output_path: str = config.get("output_folder")
        self.source_language: str = config.get("source_language")
        self.target_language: str = config.get("target_language")

    # 读取
    def read_from_path(self, abs_paths: list[str]) -> list[CacheItem]:
        items:list[CacheItem] = []
        for abs_path in abs_paths:
            # 获取相对路径
            rel_path = os.path.relpath(abs_path, self.input_path)

            # 数据处理
            book: openpyxl.Workbook = openpyxl.load_workbook(abs_path)
            sheet: openpyxl.worksheet.worksheet.Worksheet = book.active

            # 跳过空表格
            if sheet.max_row == 0 or sheet.max_column == 0:
                continue

            # 判断是否为 WOLF 翻译表格文件
            if not self.is_wold_xlsx(sheet):
                continue

            for row in range(2, sheet.max_row + 1):
                src: str = sheet.cell(row = row, column = 6).value
                dst: str = sheet.cell(row = row, column = 7).value

                # 跳过读取失败的行
                # 数据不存在时为 None，存在时可能是 str int float 等多种类型
                if src is None:
                    continue

                src: str = str(src)
                dst: str = str(dst) if dst is not None else ""

                if (
                    src == ""
                    or self.get_fg_color_index(sheet, row, 6) not in WOLFXLSX.FILL_COLOR_WHITELIST
                ):
                    items.append(
                        CacheItem({
                            "src": src,
                            "dst": dst,
                            "row": row,
                            "file_type": CacheItem.FileType.WOLFXLSX,
                            "file_path": rel_path,
                            "text_type": CacheItem.TextType.WOLF,
                            "status": Base.TranslationStatus.EXCLUDED,
                        })
                    )
                elif dst != "" and src != dst:
                    items.append(
                        CacheItem({
                            "src": src,
                            "dst": dst,
                            "row": row,
                            "file_type": CacheItem.FileType.WOLFXLSX,
                            "file_path": rel_path,
                            "text_type": CacheItem.TextType.WOLF,
                            "status": Base.TranslationStatus.TRANSLATED_IN_PAST,
                        })
                    )
                else:
                    items.append(
                        CacheItem({
                            "src": src,
                            "dst": dst,
                            "row": row,
                            "file_type": CacheItem.FileType.WOLFXLSX,
                            "file_path": rel_path,
                            "text_type": CacheItem.TextType.WOLF,
                            "status": Base.TranslationStatus.UNTRANSLATED,
                        })
                    )

        return items

    # 是否为 WOLF 翻译表格文件
    def is_wold_xlsx(self, sheet: openpyxl.worksheet.worksheet.Worksheet) -> bool:
        value: str = sheet.cell(row = 1, column = 1).value
        if not isinstance(value, str) or "code" not in value.lower():
            return False

        value: str = sheet.cell(row = 1, column = 2).value
        if not isinstance(value, str) or "flag" not in value.lower():
            return False

        value: str = sheet.cell(row = 1, column = 3).value
        if not isinstance(value, str) or "type" not in value.lower():
            return False

        value: str = sheet.cell(row = 1, column = 4).value
        if not isinstance(value, str) or "info" not in value.lower():
            return False

        return True

    # 获取单元格填充颜色索引
    def get_fg_color_index(self, sheet: openpyxl.worksheet.worksheet.Worksheet, row: int, column: int) -> int:
        fill = sheet.cell(row = row, column = column).fill
        if fill.fill_type is not None:
            fg_color = fill.fgColor
            if fg_color:
                if isinstance(fg_color, openpyxl.styles.Color):
                    if fg_color.type == "indexed":
                        return fg_color.indexed

        return -1