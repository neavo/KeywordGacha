import re

class RENPY():

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

    def __init__(self) -> None:
        super().__init__()

    # 读取名称和数据
    def read_from_path(self, abs_paths: list[str]) -> list[str]:
        items: list[str] = []
        for abs_path in set(abs_paths):
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
                    name = ""
                elif is_content_line == True and len(results) >= 2:
                    src = results[1].replace("\\n", "\n").replace("\\\"", "\"")
                    name = results[0]
                else:
                    src = ""
                    name = ""

                # 添加数据
                if name == "":
                    items.append(src)
                else:
                    items.append(f"【{name}】{src}")

        return items