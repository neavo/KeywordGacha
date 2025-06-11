import json
import os
import random
from datetime import datetime

import openpyxl
import openpyxl.worksheet.worksheet

from base.Base import Base
from model.Item import Item
from model.Project import Project
from module.Config import Config
from module.File.ASS import ASS
from module.File.EPUB import EPUB
from module.File.KVJSON import KVJSON
from module.File.MD import MD
from module.File.MESSAGEJSON import MESSAGEJSON
from module.File.RENPY import RENPY
from module.File.SRT import SRT
from module.File.TRANS.TRANS import TRANS
from module.File.TXT import TXT
from module.File.WOLFXLSX import WOLFXLSX
from module.File.XLSX import XLSX
from module.Localizer.Localizer import Localizer
from module.TableManager import TableManager

class FileManager(Base):

    def __init__(self, config: Config) -> None:
        super().__init__()

        # 初始化
        self.config = config

    # 读
    def read_from_path(self) -> tuple[Project, list[Item]]:
        project: Project = Project.from_dict({
            "id": f"{datetime.now().strftime("%Y%m%d_%H%M%S")}_{random.randint(100000, 999999)}",
        })

        items: list[Item] = []
        try:
            paths: list[str] = []
            input_folder: str = self.config.input_folder
            if os.path.isfile(input_folder):
                paths = [input_folder]
            elif os.path.isdir(input_folder):
                for root, _, files in os.walk(input_folder):
                    paths.extend([f"{root}/{file}".replace("\\", "/") for file in files])

            items.extend(MD(self.config).read_from_path([path for path in paths if path.lower().endswith(".md")]))
            items.extend(TXT(self.config).read_from_path([path for path in paths if path.lower().endswith(".txt")]))
            items.extend(ASS(self.config).read_from_path([path for path in paths if path.lower().endswith(".ass")]))
            items.extend(SRT(self.config).read_from_path([path for path in paths if path.lower().endswith(".srt")]))
            items.extend(EPUB(self.config).read_from_path([path for path in paths if path.lower().endswith(".epub")]))
            items.extend(XLSX(self.config).read_from_path([path for path in paths if path.lower().endswith(".xlsx")]))
            items.extend(WOLFXLSX(self.config).read_from_path([path for path in paths if path.lower().endswith(".xlsx")]))
            items.extend(RENPY(self.config).read_from_path([path for path in paths if path.lower().endswith(".rpy")]))
            items.extend(TRANS(self.config).read_from_path([path for path in paths if path.lower().endswith(".trans")]))
            items.extend(KVJSON(self.config).read_from_path([path for path in paths if path.lower().endswith(".json")]))
            items.extend(MESSAGEJSON(self.config).read_from_path([path for path in paths if path.lower().endswith(".json")]))
        except Exception as e:
            self.error(f"{Localizer.get().log_read_file_fail}", e)

        return project, items

    # 导出
    def write_to_path(self, glossary: list[dict[str, str | int | list[str]]]) -> None:
        try:
            # 新建工作表
            book: openpyxl.Workbook = openpyxl.Workbook()
            sheet: openpyxl.worksheet.worksheet.Worksheet = book.active

            # 设置表头
            sheet.column_dimensions["A"].width = 32
            sheet.column_dimensions["B"].width = 32
            sheet.column_dimensions["C"].width = 32
            sheet.column_dimensions["D"].width = 32
            sheet.column_dimensions["E"].width = 32
            TableManager.set_cell_value(sheet, 1, 1, "src", 10)
            TableManager.set_cell_value(sheet, 1, 2, "dst", 10)
            TableManager.set_cell_value(sheet, 1, 3, "info", 10)
            TableManager.set_cell_value(sheet, 1, 4, "regex", 10)
            TableManager.set_cell_value(sheet, 1, 5, "count", 10)

            # 启用表头筛选
            sheet.auto_filter.ref = "A1:E1"

            # 将数据写入工作表
            for row, item in enumerate(glossary):
                TableManager.set_cell_value(sheet, row + 2, 1, item.get("src", ""), 10)
                TableManager.set_cell_value(sheet, row + 2, 2, item.get("dst", ""), 10)
                TableManager.set_cell_value(sheet, row + 2, 3, item.get("info", ""), 10)
                TableManager.set_cell_value(sheet, row + 2, 4, item.get("regex", ""), 10)
                TableManager.set_cell_value(sheet, row + 2, 5, item.get("count", 0), 10)

            # 保存工作簿
            book.save(f"{self.config.output_folder}/output.xlsx")

            # 保存日志
            with open(f"{self.config.output_folder}/output_log.txt", "w", encoding = "utf-8") as writer:
                for entry in glossary:
                    src: str = entry.get("src", "")
                    dst: str = entry.get("dst", "")
                    count: int = entry.get("count", 0)
                    context: list[str] = entry.get("context", [])[:10]

                    # 写入文件
                    writer.write(f"{Localizer.get().ner_output_log_src}{src}" + "\n")
                    writer.write(f"{Localizer.get().ner_output_log_dst}{dst}" + "\n")
                    writer.write(f"{Localizer.get().ner_output_log_count}{count}" + "\n")
                    writer.write(f"{Localizer.get().ner_output_log_context}※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※" + "\n")
                    writer.write("\n".join(context) + "\n")
                    writer.write("\n")

            # 保存 JSON
            [v.pop("context", None) for v in glossary]
            with open(f"{self.config.output_folder}/output.json", "w", encoding = "utf-8") as writer:
                writer.write(json.dumps(glossary, indent = 4, ensure_ascii = False))
        except Exception as e:
            self.error(f"{Localizer.get().log_read_file_fail}", e)