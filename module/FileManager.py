import os
import re
import csv
import json
import warnings

import ebooklib
import openpyxl
from bs4 import BeautifulSoup
from ebooklib import epub

from model.NER import NER
from model.Word import Word
from module.LogHelper import LogHelper
from module.Normalizer import Normalizer
from module.TextHelper import TextHelper

class FileManager():

    # https://github.com/aerkalov/ebooklib/issues/296
    warnings.filterwarnings(
        "ignore",
        message = "In the future version we will turn default option ignore_ncx to True."
    )
    warnings.filterwarnings(
        "ignore",
        message = "This search incorrectly ignores the root element, and will be fixed in a future version"
    )

    def __init__(self) -> None:
        super().__init__()

    # 加载角色数据
    def load_names(self, path: str) -> tuple[dict, dict]:
        names = {}
        nicknames = {}

        if os.path.exists(path):
            with open(path, "r", encoding = "utf-8") as reader:
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
        items = []
        try:
            if os.path.isfile(input_path):
                paths = [input_path]
            elif os.path.isdir(input_path):
                paths = [os.path.join(root, file).replace("\\", "/").lower() for root, _, files in os.walk(input_path) for file in files]

            items.extend(self.read_from_path_txt(input_path, [path for path in paths if path.endswith(".txt")]))
            items.extend(self.read_from_path_ass(input_path, [path for path in paths if path.endswith(".ass")]))
            items.extend(self.read_from_path_srt(input_path, [path for path in paths if path.endswith(".srt")]))
            items.extend(self.read_from_path_csv(input_path, [path for path in paths if path.endswith(".csv")]))
            items.extend(self.read_from_path_xlsx(input_path, [path for path in paths if path.endswith(".xlsx")]))
            items.extend(self.read_from_path_epub(input_path, [path for path in paths if path.endswith(".epub")]))
            items.extend(self.read_from_path_renpy(input_path, [path for path in paths if path.endswith(".renpy")]))
            items.extend(self.read_from_path_kvjson(input_path, [path for path in paths if path.endswith(".json")]))
            items.extend(self.read_from_path_messagejson(input_path, [path for path in paths if path.endswith(".json")]))
        except Exception as e:
            LogHelper.error(f"文件读取失败 ... {e}")

        return items

    # TXT
    def read_from_path_txt(self, input_path: str, abs_paths: list[str]) -> list[str]:
        items = []
        for abs_path in set(abs_paths):
            # 数据处理
            with open(abs_path, "r", encoding = "utf-8") as reader:
                for line in [line.removesuffix("\n") for line in reader.readlines()]:
                    items.append(line)

        return items

    # ASS
    def read_from_path_ass(self, input_path: str, abs_paths: list[str]) -> list[str]:
        # [Script Info]
        # ; This is an Advanced Sub Station Alpha v4+ script.
        # Title:
        # ScriptType: v4.00+
        # PlayDepth: 0
        # ScaledBorderAndShadow: Yes

        # [V4+ Styles]
        # Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
        # Style: Default,Arial,20,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,1,2,10,10,10,1

        # [Events]
        # Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
        # Dialogue: 0,0:00:08.12,0:00:10.46,Default,,0,0,0,,にゃにゃにゃ
        # Dialogue: 0,0:00:14.00,0:00:15.88,Default,,0,0,0,,えーこの部屋一人で使\Nえるとか最高じゃん
        # Dialogue: 0,0:00:15.88,0:00:17.30,Default,,0,0,0,,えるとか最高じゃん

        items = []
        for abs_path in set(abs_paths):
            # 数据处理
            with open(abs_path, "r", encoding = "utf-8") as reader:
                lines = [line.strip() for line in reader.readlines()]

                # 格式字段的数量
                in_event = False
                format_field_num = -1
                for line in lines:
                    # 判断是否进入事件块
                    if line == "[Events]":
                        in_event = True
                    # 在事件块中寻找格式字段
                    if in_event == True and line.startswith("Format:"):
                        format_field_num = len(line.split(",")) - 1
                        break

                for line in lines:
                    content = ",".join(line.split(",")[format_field_num:]) if line.startswith("Dialogue:") else ""

                    # 添加数据
                    items.append(content.replace("\\N", "\n"))

        return items

    # SRT
    def read_from_path_srt(self, input_path: str, abs_paths: list[str]) -> list[str]:
        # 1
        # 00:00:08,120 --> 00:00:10,460
        # にゃにゃにゃ

        # 2
        # 00:00:14,000 --> 00:00:15,880
        # えーこの部屋一人で使

        # 3
        # 00:00:15,880 --> 00:00:17,300
        # えるとか最高じゃん

        items = []
        for abs_path in set(abs_paths):
            # 数据处理
            with open(abs_path, "r", encoding = "utf-8") as reader:
                chunks = re.split(r"\n{2,}", reader.read().strip())
                for chunk in chunks:
                    lines = chunk.splitlines()

                    # 格式校验
                    # isdigit
                    # 仅返回 True 如果字符串中的所有字符都是 Unicode 数字字符（例如：0-9），不包括带有上标的数字（如 ²）或带分隔符的数字（如罗马数字）。
                    # isnumeric
                    # 返回 True 如果字符串中的所有字符都是 Unicode 数值字符，包括 Unicode 数字、带有上标的数字和其他形式的数值字符（如罗马数字）。
                    if len(lines) < 3 or not lines[0].isdigit():
                        continue

                    # 添加数据
                    if lines[-1] != "":
                        items.append("\n".join(lines[2:]))

        return items

    # CSV
    def read_from_path_csv(self, input_path: str, abs_paths: list[str]) -> list[str]:
        items = []
        for abs_path in set(abs_paths):
            with open(abs_path, "r", newline = "", encoding = "utf-8") as file:
                for row in csv.reader(file):
                    items.append(row[0])

        return items

    # XLSX
    def read_from_path_xlsx(self, input_path: str, abs_paths: list[str]) -> list[str]:
        items = []
        for abs_path in set(abs_paths):
            # 数据处理
            wb = openpyxl.load_workbook(abs_path)
            sheet = wb.active

            # 跳过空表格
            if sheet.max_column == 0:
                continue

            for row in range(1, sheet.max_row + 1):
                src = sheet.cell(row = row, column = 1).value

                # 跳过读取失败的行
                if src is None:
                    continue

                items.append(str(src))

        return items

    # EPUB
    def read_from_path_epub(self, input_path: str, abs_paths: list[str]) -> list[str]:
        items = []
        for abs_path in set(abs_paths):
            # 数据处理
            book = epub.read_epub(abs_path)
            for doc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                bs = BeautifulSoup(doc.get_content(), "html.parser")
                for line in bs.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"]):
                    items.append(line.get_text())

        return items

    # RENPY
    def read_from_path_renpy(self, input_path: str, abs_paths: list[str]) -> list[str]:
        # # game/script8.rpy:16878
        # translate chinese arabialogoff_e5798d9a:
        #
        #     # lo "And you...?{w=2.3}{nw}" with dissolve
        #     lo "And you...?{w=2.3}{nw}" with dissolve
        #
        # # game/script/1-home/1-Perso_Home/elice.rpy:281
        # translate schinese elice_ask_home_f01e3240_5:
        #
        #     # e ".{w=0.5}.{w=0.5}.{w=0.5}{nw}"
        #     e ".{w=0.5}.{w=0.5}.{w=0.5}{nw}"
        #
        # # game/script8.rpy:33
        # translate chinese update08_a626b58f:
        #
        #     # "*Snorts* Fucking hell, I hate this dumpster of a place." with dis06
        #     "*Snorts* Fucking hell, I hate this dumpster of a place." with dis06
        #
        # translate chinese strings:
        #
        #     # game/script8.rpy:307
        #     old "Accompany her to the inn"
        #     new "Accompany her to the inn"
        #
        #     # game/script8.rpy:2173
        #     old "{sc=3}{size=44}Jump off the ship.{/sc}"
        #     new "{sc=3}{size=44}Jump off the ship.{/sc}"

        # 查找文本中最后一对双引号包裹的文本
        def find_content(text: str) -> str:
            matches = re.findall(r"\"(.*?)(?<!\\)\"(?!\")", text)

            if matches:
                # 获取最后一对引号中的子串
                last_match = matches[-1]

                # 找到最后一个目标子串的位置，包括引号
                start_index = text.rfind('"' + last_match + '"')
                end_index = start_index + len('"' + last_match + '"')

                # 将剩余的字符串中目标子串的内容（不包括引号）替换为 {{CONTENT}}
                modified_str = text[: start_index + 1] + "{{CONTENT}}" + text[end_index - 1 :]

                return last_match, modified_str
            else:
                return "", text

        items = []
        for abs_path in set(abs_paths):
            # 数据处理
            with open(abs_path, "r", encoding = "utf-8") as reader:
                lines = [line.removesuffix("\n") for line in reader.readlines()]

            skip_next = False
            for line in lines:
                if skip_next == True:
                    skip_next = False
                    continue
                elif line.count("\"") >= 2 and (line.startswith("    # ") or line.startswith("    old ")):
                    skip_next = True
                    content, extra_field = find_content(line)
                    content = content.replace("\\n", "\n")
                else:
                    content = ""
                    extra_field = line

                # 添加数据
                items.append(content)

        return items

    # KV JSON
    def read_from_path_kvjson(self, input_path: str, abs_paths: list[str]) -> list[str]:
        # {
        #     "「あ・・」": "「あ・・」",
        #     "「ごめん、ここ使う？」": "「ごめん、ここ使う？」",
        #     "「じゃあ・・私は帰るね」": "「じゃあ・・私は帰るね」",
        # }

        items = []
        for abs_path in set(abs_paths):
            # 数据处理
            with open(abs_path, "r", encoding = "utf-8") as reader:
                json_data: dict[str, str] = TextHelper.safe_load_json_dict(reader.read().strip())

                # 格式校验
                if json_data == {}:
                    continue

                # 读取数据
                for k, v in json_data.items():
                    # 格式校验
                    if not isinstance(k, str) or not isinstance(v, str):
                        continue

                    if k != "":
                        items.append(k)

        return items

    # Message JSON
    def read_from_path_messagejson(self, input_path: str, abs_paths: list[str]) -> list[str]:
        # [
        #     {
        #         "message": "<fgName:pipo-fog004><fgLoopX:1><fgLoopY:1><fgSx:-2><fgSy:0.5>"
        #     },
        #     {
        #         "message": "エンディングを変更しますか？"
        #     },
        #     {
        #         "message": "はい"
        #     },
        # ]

        items = []
        for abs_path in set(abs_paths):
            # 数据处理
            with open(abs_path, "r", encoding = "utf-8") as reader:
                json_data: list[dict] = TextHelper.safe_load_json_list(reader.read().strip())

                # 格式校验
                if json_data == [] or not isinstance(json_data[0], dict):
                    continue

                for v in json_data:
                    # 格式校验
                    if "message" not in v:
                        continue

                    if v.get("message") != "":
                        items.append(f"【{v.get("name", "")}】{v.get("message")}")

        return items

    # 从输入文件中加载数据
    def load_lines_from_input_file(self, language: int) -> tuple[list, dict[int, str], dict[int, str]]:
        # 依次读取每个数据文件
        with LogHelper.status("正在读取输入文件 ..."):
            if os.path.isdir("input"):
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

                if language == NER.Language.ZH and not TextHelper.has_any_cjk(line):
                    continue
                elif language == NER.Language.EN and not TextHelper.has_any_latin(line):
                    continue
                elif language == NER.Language.JA and not TextHelper.has_any_japanese(line):
                    continue
                elif language == NER.Language.KO and not TextHelper.has_any_korean(line):
                    continue

                # 添加结果
                lines_filtered.append(line)
        LogHelper.info(f"已读取到文本 {len(lines)} 行，其中有效文本 {len(lines_filtered)} 行 ...")

        return lines_filtered, names, nicknames

    # 将 词语日志 写入文件
    def write_words_log_to_file(self, words: list[Word], path: str, language: int) -> None:
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
                    writer.write(f"{"\n".join(word.context_translation)}" + "\n")

                # 多写入一个换行符，确保每段信息之间有间隔
                writer.write("\n")

        LogHelper.info(f"结果已写入 - [green]{path}[/]")

    # 将 词语列表 写入文件
    def write_words_list_to_file(self, words: list[Word], path: str, language: int) -> None:
        with open(path, "w", encoding = "utf-8") as file:
            data = {}
            for k, word in enumerate(words):
                data[word.surface] = word.surface_translation

            file.write(json.dumps(data, indent = 4, ensure_ascii = False))
            LogHelper.info(f"结果已写入 - [green]{path}[/]")

    # 将 AiNiee 词典写入文件
    def write_glossary_dict_to_file(self, words: list[Word], path: str, language: int) -> None:
        with open(path, "w", encoding = "utf-8") as file:
            datas = []
            for word in words:
                data = {}
                data["src"] = word.surface
                data["dst"] = word.surface_translation

                if word.group == "角色" and "男" in word.gender:
                    data["info"] = "男性名字"
                elif word.group == "角色" and "女" in word.gender:
                    data["info"] = "女性名字"
                elif word.group == "角色":
                    data["info"] = "名字"
                else:
                    data["info"] = f"{word.group}"

                datas.append(data)

            file.write(json.dumps(datas, indent = 4, ensure_ascii = False))
            LogHelper.info(f"结果已写入 - [green]{path}[/]")

    # 将 GalTransl 词典写入文件
    def write_galtransl_dict_to_file(self, words: list[Word], path: str, language: int) -> None:
        with open(path, "w", encoding = "utf-8") as file:
            for word in words:
                line = f"{word.surface}\t{word.surface_translation}"

                if word.group == "角色" and "男" in word.gender:
                    line = line + "\t男性名字"
                elif word.group == "角色" and "女" in word.gender:
                    line = line + "\t女性名字"
                elif word.group == "角色":
                    line = line + "\t名字"
                else:
                    line = line + f"\t{word.group}"

                file.write(f"{line}" + "\n")
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
            self.write_words_log_to_file(words_by_type, f"output/{file_name}_{group}_日志.txt", language)
            self.write_words_list_to_file(words_by_type, f"output/{file_name}_{group}_词典.json", language)
            self.write_glossary_dict_to_file(words_by_type, f"output/{file_name}_{group}_术语表.json", language)
            self.write_galtransl_dict_to_file(words_by_type, f"output/{file_name}_{group}_galtransl.txt", language)