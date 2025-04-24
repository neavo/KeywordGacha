import os
import re

from base.Base import Base
from module.Cache.CacheItem import CacheItem

class RENPY(Base):

    # # game/script8.rpy:16878
    # translate chinese arabialogoff_e5798d9a:
    #
    #     # "lo" "And you...?{w=2.3}{nw}" with dissolve
    #     # "lo" "" with dissolve
    #
    # # game/script/1-home/1-Perso_Home/elice.rpy:281
    # translate schinese elice_ask_home_f01e3240_5:
    #
    #     # e ".{w=0.5}.{w=0.5}.{w=0.5}{nw}"
    #     e ""
    #
    # # game/script8.rpy:33
    # translate chinese update08_a626b58f:
    #
    #     # "*Snorts* Fucking hell, I hate with this dumpster of a place." with dis06
    #     "" with dis06
    #
    # translate chinese strings:
    #
    #     # game/script8.rpy:307
    #     old "Accompany her to the inn"
    #     new ""
    #
    #     # game/script8.rpy:2173
    #     old "{sc=3}{size=44}Jump off the ship.{/sc}"
    #     new ""
    #
    # # game/routes/endings/laura/normal/Harry/l_normal_11_h.rpy:3
    # translate schinese l_normal_11_h_f9190bc9:
    #
    #     # nvl clear
    #     # n "After a wonderful night, the next day, to our displeasure, we were faced with the continuation of the commotion that I had accidentally engendered the morning prior."
    #     n ""

    # 匹配 RenPy 文本的规则
    RE_RENPY = re.compile(r"\"(.*?)(?<!\\)\"(?!\")", flags = re.IGNORECASE)

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
        items: list[CacheItem] = []
        for abs_path in abs_paths:
            # 获取相对路径
            try:
                rel_path = os.path.relpath(abs_path, self.input_path)
            except Exception:
                rel_path = abs_path

            # 数据处理
            with open(abs_path, "r", encoding = "utf-8-sig") as reader:
                lines = [line.rstrip() for line in reader.readlines()]

            for i, line in enumerate(lines):
                results: list[str] = RENPY.RE_RENPY.findall(line)
                is_content_line = line.startswith("    # ") or line.startswith("    old ")

                # 不是内容行但找到匹配项目时，则直接跳过这一行
                if is_content_line == False and len(results) > 0:
                    continue
                elif is_content_line == True and len(results) == 1:
                    src = results[0].replace("\\n", "\n").replace("\\\"", "\"")
                    dst = self.find_dst(i + 1, line, lines)
                    name = None
                elif is_content_line == True and len(results) >= 2:
                    src = results[1].replace("\\n", "\n").replace("\\\"", "\"")
                    dst = self.find_dst(i + 1, line, lines)
                    name = results[0]
                else:
                    src = ""
                    dst = ""
                    name = None

                # 添加数据
                if src == "":
                    items.append(
                        CacheItem({
                            "src": src,
                            "dst": dst,
                            "name_src": name,
                            "name_dst": name,
                            "extra_field": line,
                            "row": len(items),
                            "file_type": CacheItem.FileType.RENPY,
                            "file_path": rel_path,
                            "text_type": CacheItem.TextType.RENPY,
                            "status": Base.TranslationStatus.EXCLUDED,
                        })
                    )
                elif dst != "" and src != dst:
                    items.append(
                        CacheItem({
                            "src": src,
                            "dst": dst,
                            "name_src": name,
                            "name_dst": name,
                            "extra_field": line,
                            "row": len(items),
                            "file_type": CacheItem.FileType.RENPY,
                            "file_path": rel_path,
                            "text_type": CacheItem.TextType.RENPY,
                            "status": Base.TranslationStatus.TRANSLATED_IN_PAST,
                        })
                    )
                else:
                    items.append(
                        CacheItem({
                            "src": src,
                            "dst": dst,
                            "name_src": name,
                            "name_dst": name,
                            "extra_field": line,
                            "row": len(items),
                            "file_type": CacheItem.FileType.RENPY,
                            "file_path": rel_path,
                            "text_type": CacheItem.TextType.RENPY,
                            "status": Base.TranslationStatus.UNTRANSLATED,
                        })
                    )

        return items

    # 获取译文
    def find_dst(self, start: int, line: str, lines: list[str]) -> str:
        # 越界检查
        if start >= len(lines):
            return ""

        # 遍历剩余行寻找目标数据
        line = line.removeprefix("    # ").removeprefix("    old ")
        for line_ex in lines[start:]:
            line_ex = line_ex.removeprefix("    ").removeprefix("    new ")
            results: list[str] = RENPY.RE_RENPY.findall(line_ex)
            if RENPY.RE_RENPY.sub("", line) == RENPY.RE_RENPY.sub("", line_ex):
                if len(results) == 1:
                    return results[0]
                elif len(results) >= 2:
                    return results[1]

        return ""