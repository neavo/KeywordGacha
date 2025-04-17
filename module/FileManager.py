import os
import re
import json
import openpyxl
import openpyxl.worksheet.worksheet

from base.Base import Base
from model.NER import NER
from model.Word import Word
from module.File.MD import MD
from module.File.ASS import ASS
from module.File.SRT import SRT
from module.File.TXT import TXT
from module.File.EPUB import EPUB
from module.File.XLSX import XLSX
from module.File.WOLFXLSX import WOLFXLSX
from module.File.RENPY import RENPY
from module.File.TRANS.TRANS import TRANS
from module.File.KVJSON import KVJSON
from module.File.MESSAGEJSON import MESSAGEJSON
from module.Text.TextHelper import TextHelper
from module.Cache.CacheItem import CacheItem
from module.LogHelper import LogHelper
from module.Normalizer import Normalizer
from module.XLSXHelper import XLSXHelper

class FileManager():

    # 去重
    RE_DUPLICATE = re.compile(r"[\r\n]+", flags = re.IGNORECASE)

    def __init__(self) -> None:
        super().__init__()

    # 加载角色数据
    def load_names(self, path: str) -> tuple[dict, dict]:
        names = {}
        nicknames = {}

        if os.path.exists(path):
            with open(path, "r", encoding = "utf-8-sig") as reader:
                for item in json.load(reader):
                    if isinstance(item, dict):
                        id = item.get("id", -1)

                        if not isinstance(id, int):
                            continue

                        names[id] = item.get("name", "")
                        nicknames[id] = item.get("nickname", "")
            LogHelper.info(f"从 [green]Actors.json[/] 文件中加载了 {len(names) + len(nicknames)} 条数据，稍后将执行 [green]角色代码还原[/] 步骤 ...")

        return names, nicknames

    # 清理文本
    def cleanup(self, line: str, language: int) -> str:
        # 由于上面的代码移除，可能会产生空人名框的情况，干掉
        line = line.replace("【】", "")

        # 干掉除了空格以外的行内空白符（包括换行符、制表符、回车符、换页符等）
        line = re.sub(r"[^\S ]+", "", line)

        # 合并连续的空格为一个空格
        line = re.sub(r" +", " ", line)

        return line

    # 读
    def read_from_path(self, input_path: str) -> list[str]:
        items: list[CacheItem] = []
        try:
            paths: list[str] = []
            if os.path.isfile(input_path):
                paths = [input_path]
            elif os.path.isdir(input_path):
                for root, _, files in os.walk(input_path):
                    paths.extend([f"{root}/{file}".replace("\\", "/") for file in files])

            # 伪数据
            config: dict[str, str] = {
                "input_folder": "",
                "output_folder": "",
                "source_language": "",
                "target_language": ""
            }

            items.extend(MD(config).read_from_path([path for path in paths if path.lower().endswith(".md")]))
            items.extend(TXT(config).read_from_path([path for path in paths if path.lower().endswith(".txt")]))
            items.extend(ASS(config).read_from_path([path for path in paths if path.lower().endswith(".ass")]))
            items.extend(SRT(config).read_from_path([path for path in paths if path.lower().endswith(".srt")]))
            items.extend(EPUB(config).read_from_path([path for path in paths if path.lower().endswith(".epub")]))
            items.extend(XLSX(config).read_from_path([path for path in paths if path.lower().endswith(".xlsx")]))
            items.extend(WOLFXLSX(config).read_from_path([path for path in paths if path.lower().endswith(".xlsx")]))
            items.extend(RENPY(config).read_from_path([path for path in paths if path.lower().endswith(".rpy")]))
            items.extend(TRANS(config).read_from_path([path for path in paths if path.lower().endswith(".trans")]))
            items.extend(KVJSON(config).read_from_path([path for path in paths if path.lower().endswith(".json")]))
            items.extend(MESSAGEJSON(config).read_from_path([path for path in paths if path.lower().endswith(".json")]))
        except Exception as e:
            LogHelper.error(f"文件读取失败 ... {e}")

        return [
            v.get_src().strip()
            for v in items if v.get_status() != Base.TranslationStatus.EXCLUDED and v.get_src().strip() != ""
        ]

    # 从输入文件中加载数据
    def read_lines_from_input_file(self, language: int) -> tuple[list, dict[int, str], dict[int, str]]:
        # 依次读取每个数据文件
        with LogHelper.status("正在读取输入文件 ..."):
            lines = self.read_from_path("input")

        # 分别处理找到和没找到的情况
        if len(lines) == 0:
            self.input_path = LogHelper.input("请输入数据文件的路径: ").strip('"')
        else:
            user_input = LogHelper.input(f"已在 [green]input[/] 路径下找到数据 [green]{len(lines)}[/] 条，按回车直接使用或输入其他路径：").strip('"')
            self.input_path = user_input if user_input != "" else "input"
        LogHelper.print("")

        # 尝试从输入路径的同级路径或者下级路径加载角色数据，找不到则生成伪数据
        names, nicknames = {}, {}
        if os.path.isfile(f"{self.input_path}/Actors.json"):
            names, nicknames = self.load_names(f"{self.input_path}/Actors.json")
        elif os.path.isfile(f"{os.path.dirname(self.input_path)}/Actors.json"):
            names, nicknames = self.load_names(f"{os.path.dirname(self.input_path)}/Actors.json")

        # 依次读取每个数据文件
        with LogHelper.status("正在读取输入文件 ..."):
            if self.input_path != "input":
                lines = self.read_from_path(self.input_path)

            lines_filtered = []
            for line in lines:
                line = Normalizer.normalize(line, merge_space = True)
                line = self.cleanup(line, language)

                if len(line) == 0:
                    continue

                if language == NER.Language.ZH and not TextHelper.CJK.any(line):
                    continue
                elif language == NER.Language.EN and not TextHelper.Latin.any(line):
                    continue
                elif language == NER.Language.JA and not TextHelper.JA.any(line):
                    continue
                elif language == NER.Language.KO and not TextHelper.KO.any(line):
                    continue

                # 添加结果
                lines_filtered.append(line)
        LogHelper.info(f"已读取到文本 {len(lines)} 行，其中有效文本 {len(lines_filtered)} 行 ...")

        return lines_filtered, names, nicknames

    # 将 词语日志 写入文件
    def write_log_to_file(self, words: list[Word], path: str, language: int) -> None:
        with open(path, "w", encoding = "utf-8") as writer:
            for k, word in enumerate(words):
                if getattr(word, "surface", "") != "":
                    writer.write(f"词语原文 : {word.surface}" + "\n")

                if getattr(word, "score", 0.0) >= 0:
                    writer.write(f"置信度 : {word.score:.4f}" + "\n")

                if getattr(word, "surface_romaji", "") != "":
                    writer.write(f"罗马音 : {word.surface_romaji}" + "\n")

                if getattr(word, "count", 0) >= 0:
                    writer.write(f"出现次数 : {word.count}" + "\n")

                if getattr(word, "surface_translation", "") != "":
                    writer.write(f"词语翻译 : {word.surface_translation}" + "\n")

                if getattr(word, "gender", "") != "":
                    writer.write(f"角色性别 : {word.gender}" + "\n")

                if getattr(word, "context_summary", "") != "":
                    writer.write(f"语义分析 : {word.context_summary}" + "\n")

                if len(getattr(word, "context", [])) > 0:
                    writer.write("参考文本原文 : ※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※" + "\n")
                    writer.write(f"{word.get_context_str_for_translate(language)}" + "\n")

                if len(getattr(word, "context_translation", [])) > 0:
                    writer.write("参考文本翻译 : ※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※" + "\n")
                    writer.write(f"{FileManager.RE_DUPLICATE.sub("\n", "\n".join(word.context_translation))}" + "\n")

                # 多写入一个换行符，确保每段信息之间有间隔
                writer.write("\n")

        LogHelper.info(f"结果已写入 - [green]{path}[/]")

    # 写入文件
    def write_glossary_to_json_file(self, words: list[Word], path: str, language: int) -> None:
        with open(path, "w", encoding = "utf-8") as file:
            datas = []
            for word in words:
                data = {}
                data["src"] = word.surface
                data["dst"] = word.surface_translation

                if word.group == "角色" and "男" in word.gender:
                    data["info"] = "男性"
                elif word.group == "角色" and "女" in word.gender:
                    data["info"] = "女性"
                elif word.group == "角色":
                    data["info"] = "名字"
                else:
                    data["info"] = f"{word.group}"

                datas.append(data)

            file.write(json.dumps(datas, indent = 4, ensure_ascii = False))
            LogHelper.info(f"结果已写入 - [green]{path}[/]")

    # 写入文件
    def write_glossary_to_xlsx_file(self, words: list[Word], path: str, language: int) -> None:
        # 新建工作表
        book: openpyxl.Workbook = openpyxl.Workbook()
        sheet: openpyxl.worksheet.worksheet.Worksheet = book.active

        # 设置表头
        sheet.column_dimensions["A"].width = 32
        sheet.column_dimensions["B"].width = 32
        sheet.column_dimensions["C"].width = 32
        sheet.column_dimensions["D"].width = 32
        XLSXHelper.set_cell_value(sheet, 1, 1, "src", 10)
        XLSXHelper.set_cell_value(sheet, 1, 2, "dst", 10)
        XLSXHelper.set_cell_value(sheet, 1, 3, "info", 10)
        XLSXHelper.set_cell_value(sheet, 1, 4, "regex", 10)

        # 将数据写入工作表
        for row, word in enumerate(words):
            if word.group == "角色" and "男" in word.gender:
                info = "男性"
            elif word.group == "角色" and "女" in word.gender:
                info = "女性"
            elif word.group == "角色":
                info = "名字"
            else:
                info = word.group

            XLSXHelper.set_cell_value(sheet, row + 2, 1, word.surface, 10)
            XLSXHelper.set_cell_value(sheet, row + 2, 2, word.surface_translation, 10)
            XLSXHelper.set_cell_value(sheet, row + 2, 3, info, 10)
            XLSXHelper.set_cell_value(sheet, row + 2, 4, "False", 10)

        # 保存工作簿
        book.save(path)
        LogHelper.info(f"结果已写入 - [green]{path}[/]")

    # 将结果写入文件
    def write_result_to_file(self, words: list[Word], language: int) -> None:
        # 获取输出路径
        os.makedirs("output", exist_ok = True)
        file_name, _ = os.path.splitext(os.path.basename(self.input_path))

        # 清理一下
        [
            os.remove(entry.path)
            for entry in os.scandir("output")
            if entry.is_file() and f"{file_name}_" in entry.path
        ]

        for group in {word.group for word in words}:
            words_by_type = [word for word in words if word.group == group]

            # 检查数据有效性
            if len(words_by_type) == 0:
                continue

            # 写入文件
            prefix = f"output/{file_name}_{group}"
            self.write_log_to_file(words_by_type, f"{prefix}_日志.txt", language)
            self.write_glossary_to_json_file(words_by_type, f"{prefix}_术语表.json", language)
            self.write_glossary_to_xlsx_file(words_by_type, f"{prefix}_术语表.xlsx", language)