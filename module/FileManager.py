import os
import re
import csv
import json

import openpyxl

from model.NER import NER
from model.Word import Word
from module.LogHelper import LogHelper
from module.Normalizer import Normalizer
from module.TextHelper import TextHelper

class FileManager():

    NAMES = {
        1: "司三七",
        2: "司五六",
        3: "司二十",
        4: "司一九",
        5: "司四八",
        6: "宇五六",
        7: "宇一七",
        8: "宇三十",
        9: "宇二九",
        10: "宇四八",
        11: "端三七",
        12: "端五六",
        13: "端四十",
        14: "端一九",
        15: "端二八",
        16: "狄四十",
        17: "狄一七",
        18: "狄二九",
        19: "狄五八",
        20: "狄三六",
        21: "慕四六",
        22: "慕一七",
        23: "慕二八",
        24: "慕五十",
        25: "慕三九",
        26: "闾三七",
        27: "闾四九",
        28: "闾二六",
        29: "闾一八",
        30: "闾五十",
        31: "诸三六",
        32: "诸二十",
        33: "诸四七",
        34: "诸一九",
        35: "诸五八",
        36: "公五九",
        37: "公二七",
        38: "公三六",
        39: "公一八",
        40: "公四十",
        41: "令一十",
        42: "令二九",
        43: "令五六",
        44: "令三七",
        45: "令四八",
        46: "屠五十",
        47: "屠一七",
        48: "屠二八",
        49: "屠四六",
        50: "屠三九",
        51: "钟四七",
        52: "钟三八",
        53: "钟一十",
        54: "钟二九",
        55: "钟五六",
        56: "胡一六",
        57: "胡二七",
        58: "胡三十",
        59: "胡四八",
        60: "胡五九",
        61: "亓五八",
        62: "亓三六",
        63: "亓四七",
        64: "亓二十",
        65: "亓一九",
        66: "翟五九",
        67: "翟四七",
        68: "翟二十",
        69: "翟一六",
        70: "翟三八",
        71: "贾二九",
        72: "贾一八",
        73: "贾四十",
        74: "贾三六",
        75: "贾五七",
        76: "褚三十",
        77: "褚二六",
        78: "褚一九",
        79: "褚四八",
        80: "褚五七",
        81: "解一八",
        82: "解二十",
        83: "解三九",
        84: "解五六",
        85: "解四七",
        86: "习二八",
        87: "习三六",
        88: "习一七",
        89: "习五十",
        90: "习四九",
        91: "汲四八",
        92: "汲三九",
        93: "汲二十",
        94: "汲一六",
        95: "汲五七",
        96: "鞠三九",
        97: "鞠五十",
        98: "鞠二六",
        99: "鞠一七",
        100: "鞠四八",
    }

    NICKNAMES = {
        1: "毛五十",
        2: "毛二七",
        3: "毛三九",
        4: "毛一六",
        5: "毛四八",
        6: "章二六",
        7: "章四八",
        8: "章三七",
        9: "章一十",
        10: "章五九",
        11: "范五十",
        12: "范一八",
        13: "范二七",
        14: "范三九",
        15: "范四六",
        16: "丁四九",
        17: "丁二十",
        18: "丁五八",
        19: "丁一七",
        20: "丁三六",
        21: "孟二八",
        22: "孟五六",
        23: "孟四九",
        24: "孟一七",
        25: "孟三十",
        26: "邹五九",
        27: "邹二六",
        28: "邹三十",
        29: "邹四八",
        30: "邹一七",
        31: "毕五九",
        32: "毕四六",
        33: "毕一十",
        34: "毕二七",
        35: "毕三八",
        36: "龚三八",
        37: "龚二九",
        38: "龚四十",
        39: "龚一七",
        40: "龚五六",
        41: "罗二八",
        42: "罗一九",
        43: "罗三六",
        44: "罗四七",
        45: "罗五十",
        46: "牛四七",
        47: "牛五十",
        48: "牛一八",
        49: "牛三九",
        50: "牛二六",
        51: "柯二十",
        52: "柯一九",
        53: "柯三八",
        54: "柯五七",
        55: "柯四六",
        56: "齐四七",
        57: "齐二九",
        58: "齐一八",
        59: "齐三十",
        60: "齐五六",
        61: "连三七",
        62: "连二九",
        63: "连一八",
        64: "连五六",
        65: "连四十",
        66: "龍五六",
        67: "龍四七",
        68: "龍二十",
        69: "龍一九",
        70: "龍三八",
        71: "吕一六",
        72: "吕四九",
        73: "吕五七",
        74: "吕三八",
        75: "吕二十",
        76: "阮二九",
        77: "阮一六",
        78: "阮五八",
        79: "阮三十",
        80: "阮四七",
        81: "方五八",
        82: "方二七",
        83: "方四十",
        84: "方三九",
        85: "方一六",
        86: "汤三八",
        87: "汤一七",
        88: "汤四六",
        89: "汤二十",
        90: "汤五九",
        91: "连四九",
        92: "连一六",
        93: "连二八",
        94: "连三七",
        95: "连五十",
        96: "邵一九",
        97: "邵五六",
        98: "邵三十",
        99: "邵四八",
    }

    # 可能存在的空字符
    SPACE_PATTERN = r""

    # 用于英文的代码段规则
    CODE_PATTERN_EN = (
        SPACE_PATTERN + r"if\(.{0,5}[vs]\[\d+\].{0,10}\)" + SPACE_PATTERN,            # if(!s[982]) if(s[1623]) if(v[982] >= 1)
        SPACE_PATTERN + r"en\(.{0,5}[vs]\[\d+\].{0,10}\)" + SPACE_PATTERN,            # en(!s[982]) en(v[982] >= 1)
        SPACE_PATTERN + r"[/\\][a-z]{1,5}<[\d]{0,10}>" + SPACE_PATTERN,               # /C<1> \FS<12>
        SPACE_PATTERN + r"[/\\][a-z]{1,5}\[[\d]{0,10}\]" + SPACE_PATTERN,             # /C[1] \FS[12]
        SPACE_PATTERN + r"[/\\][a-z]{1,5}(?=<[^\d]{0,10}>)" + SPACE_PATTERN,          # /C<非数字> \FS<非数字> 中的前半部分
        SPACE_PATTERN + r"[/\\][a-z]{1,5}(?=\[[^\d]{0,10}\])" + SPACE_PATTERN,        # /C[非数字] \FS[非数字] 中的前半部分
    )

    # 用于非英文的代码段规则
    CODE_PATTERN_NON_EN = (
        SPACE_PATTERN + r"if\(.{0,5}[vs]\[\d+\].{0,10}\)" + SPACE_PATTERN,            # if(!s[982]) if(v[982] >= 1) if(v[982] >= 1)
        SPACE_PATTERN + r"en\(.{0,5}[vs]\[\d+\].{0,10}\)" + SPACE_PATTERN,            # en(!s[982]) en(v[982] >= 1)
        SPACE_PATTERN + r"[/\\][a-z]{1,5}<[a-z\d]{0,10}>" + SPACE_PATTERN,            # /C<y> /C<1> \FS<xy> \FS<12>
        SPACE_PATTERN + r"[/\\][a-z]{1,5}\[[a-z\d]{0,10}\]" + SPACE_PATTERN,          # /C[x] /C[1] \FS[xy] \FS[12]
        SPACE_PATTERN + r"[/\\][a-z]{1,5}(?=<[^a-z\d]{0,10}>)" + SPACE_PATTERN,       # /C<非数字非字母> \FS<非数字非字母> 中的前半部分
        SPACE_PATTERN + r"[/\\][a-z]{1,5}(?=\[[^a-z\d]{0,10}\])" + SPACE_PATTERN,     # /C[非数字非字母] \FS[非数字非字母] 中的前半部分
    )

    # 同时作用于英文于非英文的代码段规则
    CODE_PATTERN_COMMON = (
        SPACE_PATTERN + r"\\fr" + SPACE_PATTERN,                                      # 重置文本的改变
        SPACE_PATTERN + r"\\fb" + SPACE_PATTERN,                                      # 加粗
        SPACE_PATTERN + r"\\fi" + SPACE_PATTERN,                                      # 倾斜
        SPACE_PATTERN + r"\\\{" + SPACE_PATTERN,                                      # 放大字体 \{
        SPACE_PATTERN + r"\\\}" + SPACE_PATTERN,                                      # 缩小字体 \}
        SPACE_PATTERN + r"\\g" + SPACE_PATTERN,                                       # 显示货币 \G
        SPACE_PATTERN + r"\\\$" + SPACE_PATTERN,                                      # 打开金币框 \$
        SPACE_PATTERN + r"\\\." + SPACE_PATTERN,                                      # 等待0.25秒 \.
        SPACE_PATTERN + r"\\\|" + SPACE_PATTERN,                                      # 等待1秒 \|
        SPACE_PATTERN + r"\\!" + SPACE_PATTERN,                                       # 等待按钮按下 \!
        SPACE_PATTERN + r"\\>" + SPACE_PATTERN,                                       # 在同一行显示文字 \>
        # SPACE_PATTERN + r"\\<" + SPACE_PATTERN,                                     # 取消显示所有文字 \<
        SPACE_PATTERN + r"\\\^" + SPACE_PATTERN,                                      # 显示文本后不需要等待 \^
        # SPACE_PATTERN + r"\\n" + SPACE_PATTERN,                                     # 换行符 \\n
        SPACE_PATTERN + r"\r\n" + SPACE_PATTERN,                                      # 换行符 \r\n
        SPACE_PATTERN + r"\n" + SPACE_PATTERN,                                        # 换行符 \n
        SPACE_PATTERN + r"\\\\<br>" + SPACE_PATTERN,                                  # 换行符 \\<br>
        SPACE_PATTERN + r"<br>" + SPACE_PATTERN,                                      # 换行符 <br>
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

    # 将角色代码还原为角色名字
    def restore_code_to_name(self, text: str, names: dict, nicknames: dict) -> str:
        # names = names if len(names) > 0 else FileManager.NAMES
        # nicknames = nicknames if len(names) > 0 else FileManager.NICKNAMES

        # 根据 actors 中的数据还原 角色代码 \N[123] 实际指向的名字
        text = re.sub(
            r"\\n\[(\d+)\]",
            lambda match: self.restore_code_to_name_repl(match, names),
            text,
            flags = re.IGNORECASE
        )

        # 根据 actors 中的数据还原 角色代码 \NN[123] 实际指向的名字
        text = re.sub(
            r"\\nn\[(\d+)\]",
            lambda match: self.restore_code_to_name_repl(match, nicknames),
            text,
            flags = re.IGNORECASE
        )

        return text

    # 执行替换
    def restore_code_to_name_repl(self, match: re.Match, names: dict) -> str:
        i = int(match.group(1))

        # 索引在范围内则替换，不在范围内则原文返回
        if i in names:
            return names.get(i, "")
        else:
            return match.group(0)

    # 将角色名字还原为角色代码
    def restore_name_to_code(self, texts: str | list[str], names: dict, nicknames: dict) -> str:
        # 输入为字符串则转换为列表
        is_str = isinstance(texts, str)
        texts = [texts] if is_str == True else texts

        # 遍历文本并处理
        for i, _ in enumerate(texts):
            for k, v in names.items():
                texts[i] = texts[i].replace(v, f"\\n[{k}]")
            for k, v in nicknames.items():
                texts[i] = texts[i].replace(v, f"\\n[{k}]")

        return texts[0] if is_str == True else texts

    # 清理文本
    def cleanup(self, line: str, language: int, names: dict, nicknames: dict) -> str:
        # 将角色代码还原为角色名字
        line = self.restore_code_to_name(line, names, nicknames)

        # 将 队伍成员代码 \P[123] 替换为 teammate_123
        line = re.sub(r"\\p\[(\d+)\]", r"teammate_\1", line, flags = re.IGNORECASE)

        if language == NER.Language.EN:
            line = re.sub(rf"(?:{"|".join(FileManager.CODE_PATTERN_EN + FileManager.CODE_PATTERN_COMMON)})+", "", line, flags = re.IGNORECASE)
        else:
            line = re.sub(rf"(?:{"|".join(FileManager.CODE_PATTERN_NON_EN + FileManager.CODE_PATTERN_COMMON)})+", "", line, flags = re.IGNORECASE)

        # 由于上面的代码移除，可能会产生空人名框的情况，干掉
        line = line.replace("【】", "")

        # 干掉除了空格以外的行内空白符（包括换行符、制表符、回车符、换页符等）
        line = re.sub(r"[^\S ]+", "", line)

        # 合并连续的空格为一个空格
        line = re.sub(r" +", " ", line)

        return line

    # 读取 .txt 文件
    def read_txt_file(self, path: str) -> list[str]:
        # 尝试使用不同的编码读取文件
        for encoding in ("utf-8", "utf-16", "shift-jis"):
            try:
                with open(path, "r", encoding = encoding) as reader:
                    return reader.readlines()
            except UnicodeDecodeError:
                pass
            except Exception as e:
                LogHelper.error(f"读取数据文件时发生错误 - {LogHelper.get_trackback(e)}")

        # 如果所有编码都没有成功，则返回空列表
        return []

    # 读取 .csv 文件
    def read_csv_file(self, path: str) -> list[str]:
        lines = []

        try:
            with open(path, "r", newline = "", encoding = "utf-8") as file:
                for row in csv.reader(file):
                    lines.append(row[0])
        except Exception as e:
            LogHelper.error(f"读取数据文件时发生错误 - {LogHelper.get_trackback(e)}")

        return lines

    # 读取 .json 文件
    def read_json_file(self, path: str) -> list[str]:
        lines = []

        try:
            # 读取并加载JSON文件
            with open(path, "r", encoding = "utf-8") as file:
                datas = json.load(file)

                # 针对 MTool 导出文本
                # {
                #   "「お前かよ。開けて。着替えなきゃ」" : "「お前かよ。開けて。着替えなきゃ」"
                # }
                if isinstance(datas, dict):
                    for k, v in datas.items():
                        if isinstance(k, str) and isinstance(v, str):
                            lines.append(k)

                # 针对 SExtractor 导出的带name字段JSON数据
                # [{
                #   "name": "少年",
                #   "message": "「お前かよ。開けて。着替えなきゃ」"
                # }]
                if isinstance(datas, list):
                    # 确保数据是字典类型
                    for data in [data for data in datas if isinstance(data, dict)]:
                        name = data.get("name", "").strip()
                        message = data.get("message", "").strip()

                        if message == "":
                            continue

                        if name == "":
                            lines.append(message)
                        else:
                            lines.append(f"【{name}】{message}")
        except Exception as e:
            LogHelper.error(f"读取数据文件时发生错误 - {LogHelper.get_trackback(e)}")

        return lines

    # 读取 .xlsx 文件
    def read_xlsx_file(self, path: str) -> list[str]:
        lines = []

        try:
            sheet = openpyxl.load_workbook(path).active
            for row in range(1, sheet.max_row + 1):
                cell_01 = sheet.cell(row = row, column = 1).value
                if isinstance(cell_01, str) and cell_01 != "":
                    lines.append(cell_01)
        except Exception as e:
            LogHelper.error(f"读取数据文件时发生错误 - {LogHelper.get_trackback(e)}")

        return lines

    # 读取文件
    def read_file(self, path: str) -> list[str]:
        lines = []

        if path.endswith(".txt"):
            lines = self.read_txt_file(path)
        elif path.endswith(".csv"):
            lines = self.read_csv_file(path)
        elif path.endswith(".json"):
            lines = self.read_json_file(path)
        elif path.endswith(".xlsx"):
            lines = self.read_xlsx_file(path)

        return lines

    # 从输入文件中加载数据
    def load_lines_from_input_file(self, language: int) -> tuple[list, list, str]:
        # 从 input 目录内寻找目标文件
        paths = []
        if os.path.isdir("input"):
            paths = [
                entry.path
                for entry in os.scandir("input")
                if entry.is_file() and entry.path.endswith((".txt", ".csv", ".json", ".xlsx"))
            ]

        # 分别处理找到和没找到的情况
        if len(paths) == 0:
            self.input_path = LogHelper.input("请输入数据文件的路径: ").strip('"')
        else:
            user_input = LogHelper.input(f"已在 [green]input[/] 路径下找到数据文件 [green]{len(paths)}[/] 个，按回车直接使用或输入其他路径：").strip('"')
            self.input_path = user_input if len(user_input) > 0 else "input"
        LogHelper.print("")

        # 分别处理输入路径是文件和文件夹的情况
        paths = []
        if os.path.isfile(self.input_path):
            paths = [self.input_path]
        elif os.path.isdir(self.input_path):
            paths = [entry.path for entry in os.scandir(self.input_path)]
        paths = [path for path in paths if path.endswith((".txt", ".csv", ".json", ".xlsx"))]

        # 尝试从输入路径的同级路径或者下级路径加载角色数据，找不到则生成伪数据
        names, nicknames = {}, {}
        if os.path.isfile(f"{self.input_path}/Actors.json"):
            names, nicknames = self.load_names(f"{self.input_path}/Actors.json")
        elif os.path.isfile(f"{os.path.dirname(self.input_path)}/Actors.json"):
            names, nicknames = self.load_names(f"{os.path.dirname(self.input_path)}/Actors.json")

        # 依次读取每个数据文件
        with LogHelper.status("正在读取输入文件 ..."):
            input_lines = []
            for path in paths:
                input_lines.extend(self.read_file(path))

            input_lines_filtered = []
            for line in input_lines:
                line = self.cleanup(line, language, names, nicknames)

                if len(line) == 0:
                    continue

                if language == NER.Language.ZH and not TextHelper.has_any_cjk(line):
                    continue

                if language == NER.Language.EN and not TextHelper.has_any_latin(line):
                    continue

                if language == NER.Language.JA and not TextHelper.has_any_japanese(line):
                    continue

                if language == NER.Language.KO and not TextHelper.has_any_korean(line):
                    continue

                # 文本规范化
                line = Normalizer.normalize(line, merge_space = True)

                # 添加结果
                input_lines_filtered.append(line)
        LogHelper.info(f"已读取到文本 {len(input_lines)} 行，其中有效文本 {len(input_lines_filtered)} 行 ...")

        return input_lines_filtered

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
    def write_ainiee_dict_to_file(self, words: list[Word], path: str, language: int) -> None:
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

            # 将角色名字还原为角色代码
            # for word in words_by_type:
            #     for key in ("context", "context_summary", "context_translation", "surface", "surface_translation"):
            #         setattr(word, key, self.restore_name_to_code(getattr(word, key), FileManager.NAMES, FileManager.NICKNAMES))

            # 写入文件
            self.write_words_log_to_file(words_by_type, f"output/{file_name}_{group}_日志.txt", language)
            self.write_words_list_to_file(words_by_type, f"output/{file_name}_{group}_列表.json", language)
            self.write_ainiee_dict_to_file(words_by_type, f"output/{file_name}_{group}_ainiee.json", language)
            self.write_galtransl_dict_to_file(words_by_type, f"output/{file_name}_{group}_galtransl.txt", language)