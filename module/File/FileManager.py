import copy
import json
import os
import random
import re
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

    # 正则
    RE_BLANK = re.compile(r"[\r\n]+", flags = re.IGNORECASE)

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
        for entry in glossary:
            entry["dst_choices"] = list(entry.get("dst_choices", set()))
            entry["info_choices"] = list(entry.get("info_choices", set()))

        self.write_to_path_xlsx(glossary)
        self.write_to_path_json(glossary)
        self.write_to_path_detail(glossary)
        self.write_to_path_kvjson(glossary) if self.config.output_kvjson == True else None

    def write_to_path_xlsx(self, glossary: list[dict[str, str | int | list[str]]]) -> None:
        try:
            # 复制一份
            glossary = copy.deepcopy(glossary)

            # 新建工作表
            book: openpyxl.Workbook = openpyxl.Workbook()
            sheet: openpyxl.worksheet.worksheet.Worksheet = book.active

            # 设置表头
            sheet.column_dimensions["A"].width = 24
            sheet.column_dimensions["B"].width = 24
            sheet.column_dimensions["C"].width = 24
            sheet.column_dimensions["D"].width = 24
            sheet.column_dimensions["E"].width = 24
            sheet.column_dimensions["F"].width = 24
            sheet.column_dimensions["G"].width = 24

            # 启用表头筛选
            sheet.auto_filter.ref = "A1:G1"

            TableManager.set_cell_value(sheet, 1, 1, "src", 10)
            TableManager.set_cell_value(sheet, 1, 2, "dst", 10)
            TableManager.set_cell_value(sheet, 1, 3, "info", 10)
            TableManager.set_cell_value(sheet, 1, 4, "regex", 10)
            TableManager.set_cell_value(sheet, 1, 5, "count", 10)
            if self.config.output_choices == True:
                TableManager.set_cell_value(sheet, 1, 6, "dst_choices", 10)
                TableManager.set_cell_value(sheet, 1, 7, "info_choices", 10)

            # 将数据写入工作表
            for row, entry in enumerate(glossary):
                src: str = entry.get("src")
                dst: str = entry.get("dst")
                dst_choices: set[str] = entry.get("dst_choices", set())
                info: str = entry.get("info")
                info_choices: set[str] = entry.get("info_choices", set())
                count: int = entry.get("count", 0)

                TableManager.set_cell_value(sheet, row + 2, 1, src, 10)
                TableManager.set_cell_value(sheet, row + 2, 2, dst, 10)
                TableManager.set_cell_value(sheet, row + 2, 3, info, 10)
                TableManager.set_cell_value(sheet, row + 2, 4, "", 10)
                TableManager.set_cell_value(sheet, row + 2, 5, count, 10)
                if self.config.output_choices == True:
                    TableManager.set_cell_value(sheet, row + 2, 6, "\n".join(dst_choices), 10)
                    TableManager.set_cell_value(sheet, row + 2, 7, "\n".join(info_choices), 10)

            # 保存工作簿
            book.save(f"{self.config.output_folder}/output.xlsx")
        except Exception as e:
            self.error(f"{Localizer.get().log_read_file_fail}", e)

    def write_to_path_json(self, glossary: list[dict[str, str | int | list[str]]]) -> None:
        try:
            # 复制一份
            glossary = copy.deepcopy(glossary)

            if self.config.output_choices == True:
                [v.pop("context", None) for v in glossary]
            else:
                [v.pop("context", None) for v in glossary]
                [v.pop("dst_choices", None) for v in glossary]
                [v.pop("info_choices", None) for v in glossary]

            # 保存 JSON
            with open(f"{self.config.output_folder}/output.json", "w", encoding = "utf-8") as writer:
                writer.write(json.dumps(glossary, indent = 4, ensure_ascii = False))
        except Exception as e:
            self.error(f"{Localizer.get().log_read_file_fail}", e)

    def write_to_path_kvjson(self, glossary: list[dict[str, str | int | list[str]]]) -> None:
        try:
            # 复制一份
            glossary = copy.deepcopy(glossary)

            # 保存 KVJSON
            with open(f"{self.config.output_folder}/output_kv.json", "w", encoding = "utf-8") as writer:
                writer.write(json.dumps({v.get("src"): v.get("dst") for v in glossary}, indent = 4, ensure_ascii = False))
        except Exception as e:
            self.error(f"{Localizer.get().log_read_file_fail}", e)

    def write_to_path_detail(self, glossary: list[dict[str, str | int | list[str]]]) -> None:
        try:
            # 复制一份
            glossary = copy.deepcopy(glossary)

            # 保存日志
            with open(f"{self.config.output_folder}/output_detail.txt", "w", encoding = "utf-8") as writer:
                for entry in glossary:
                    src: str = entry.get("src")
                    dst: str = entry.get("dst")
                    dst_choices: set[str] = entry.get("dst_choices", set())
                    info: str = entry.get("info")
                    info_choices: set[str] = entry.get("info_choices", set())
                    count: int = entry.get("count", 0)
                    context: list[str] = entry.get("context", [])[:10]

                    # 写入文件
                    writer.write(f"{Localizer.get().ner_output_log_src}{src}" + "\n")
                    writer.write(f"{Localizer.get().ner_output_log_dst}{dst}" + "\n")
                    if self.config.output_choices == True:
                        writer.write(f"{Localizer.get().ner_output_log_dst_choices}{", ".join(dst_choices)}" + "\n")
                    writer.write(f"{Localizer.get().ner_output_log_info}{info}" + "\n")
                    if self.config.output_choices == True:
                        writer.write(f"{Localizer.get().ner_output_log_info_choices}{", ".join(info_choices)}" + "\n")
                    writer.write(f"{Localizer.get().ner_output_log_count}{count}" + "\n")
                    writer.write(f"{Localizer.get().ner_output_log_context}※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※" + "\n")
                    writer.write(__class__.RE_BLANK.sub("\n", "\n".join(context)) + "\n")
                    writer.write("\n")
        except Exception as e:
            self.error(f"{Localizer.get().log_read_file_fail}", e)
