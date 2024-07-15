import re
import json

import spacy

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper
from helper.ProgressHelper import ProgressHelper

class NER:

    TASK_MODES = type("GClass", (), {})()
    TASK_MODES.QUICK = 10
    TASK_MODES.TOTAL = 20

    SPACY_N_PROCESS = 4
    SPACY_BACTH_SIZE = 128

    NER_TYPES = {}

    NER_TYPES[TASK_MODES.QUICK] = [
            # "",             # 表示非实体，数量极多
            # "CARDINAL",     # 表示基数词，如数字"1"、"三"等。
            # "DATE",         # 表示日期，如"2024年07月11日"。
            # "EVENT",        # 表示事件，如"奥运会"、"地震"等。
            # "FAC",          # 表示设施，如"医院"、"学校"、"机场"等。
            # "GPE",          # 表示地理政治实体，如"中国"、"纽约"等。
            # "LANGUAGE",     # 表示语言，如"英语"、"汉语"等。
            # "LAW",          # 表示法律、法规，如"宪法"、"民法典"等。
            # "LOC",          # 表示地点，通常指非地理政治实体的地点，如"房间"、"街道"等。
            # "MONEY",        # 表示货币，如"100美元"、"500欧元"等。
            # "MOVEMENT",     # 表示运动或趋势，如"女权运动"、"环保运动"等。
            # "NORP",         # 表示民族或宗教组织，如"基督教"、"伊斯兰教"等。
            # "ORDINAL",      # 表示序数词，如"第一"、"第二"等。
            # "ORG",          # 表示组织，如"联合国"、"苹果公司"等。
            # "PERCENT",      # 表示百分比，如"50%"。
            "PERSON",         # 表示人名，如"张三"、"约翰·多伊"等。
            "PET_NAME",       # 表示宠物的名字，如"小白"、"Max"等。
            # "PHONE",        # 表示电话号码，如"123-456-7890"。
            # "PRODUCT",      # 表示产品，如"iPhone"、"Windows操作系统"等。
            # "QUANTITY",     # 表示数量，如"两公斤"、"三个"等。
            # "TIME",         # 表示时间，如"下午三点"、"午夜"等。
            # "TITLE_AFFIX",  # 表示头衔或后缀，如"博士"、"先生"、"女士"等。
            # "WORK_OF_ART",  # 表示艺术作品，如"蒙娜丽莎"、"悲惨世界"等。
    ]

    NER_TYPES[TASK_MODES.TOTAL] = [
            # "",           # 表示非实体，数量极多
            "CARDINAL",     # 表示基数词，如数字"1"、"三"等。
            "DATE",         # 表示日期，如"2024年07月11日"。
            "EVENT",        # 表示事件，如"奥运会"、"地震"等。
            "FAC",          # 表示设施，如"医院"、"学校"、"机场"等。
            "GPE",          # 表示地理政治实体，如"中国"、"纽约"等。
            "LANGUAGE",     # 表示语言，如"英语"、"汉语"等。
            "LAW",          # 表示法律、法规，如"宪法"、"民法典"等。
            "LOC",          # 表示地点，通常指非地理政治实体的地点，如"房间"、"街道"等。
            "MONEY",        # 表示货币，如"100美元"、"500欧元"等。
            "MOVEMENT",     # 表示运动或趋势，如"女权运动"、"环保运动"等。
            "NORP",         # 表示民族或宗教组织，如"基督教"、"伊斯兰教"等。
            "ORDINAL",      # 表示序数词，如"第一"、"第二"等。
            "ORG",          # 表示组织，如"联合国"、"苹果公司"等。
            "PERCENT",      # 表示百分比，如"50%"。
            "PERSON",       # 表示人名，如"张三"、"约翰·多伊"等。
            "PET_NAME",     # 表示宠物的名字，如"小白"、"Max"等。
            "PHONE",        # 表示电话号码，如"123-456-7890"。
            "PRODUCT",      # 表示产品，如"iPhone"、"Windows操作系统"等。
            "QUANTITY",     # 表示数量，如"两公斤"、"三个"等。
            "TIME",         # 表示时间，如"下午三点"、"午夜"等。
            "TITLE_AFFIX",  # 表示头衔或后缀，如"博士"、"先生"、"女士"等。
            "WORK_OF_ART",  # 表示艺术作品，如"蒙娜丽莎"、"悲惨世界"等。
    ]

    def __init__(self):
        self.blacklist = ""
        self.tokenizer = spacy.load(
            # "ja_core_news_lg",
            "resource\\kg_ner_ja",
            exclude = [
                "parser",
                "tok2vec",
                "morphologizer",
                "attribute_ruler"
            ]
        )

    # 从指定路径加载黑名单文件内容
    def load_blacklist(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                data = json.load(file)

                self.blacklist = ""
                for k, v in enumerate(data):
                    self.blacklist = self.blacklist + v + "\n"
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 查找 NER 实体 
    def search_for_entity(self, full_text_lines, task_mode):
        words = []

        LogHelper.print()
        with ProgressHelper.get_progress() as progress:
            pid = progress.add_task("查找 NER 实体", total = None)
            for doc in self.tokenizer.pipe(full_text_lines, n_process = self.SPACY_N_PROCESS, batch_size = self.SPACY_BACTH_SIZE):
                for token in doc:
                    word = Word()
                    word.count = 1
                    word.surface = token.lemma_
                    word.ner_type = token.ent_type_

                    # 判断词性
                    if not word.ner_type in self.NER_TYPES[task_mode]:
                        continue

                    # 移除纯汉字词
                    # if TextHelper.is_all_cjk(word.surface):
                    #     continue

                    # 移除首尾标点符号
                    word.surface = TextHelper.strip_punctuation(word.surface)

                    # 有效性检查
                    if not TextHelper.is_valid_japanese_word(word.surface, self.blacklist):
                        continue

                    words.append(word)

                progress.update(pid, advance = 1, total = len(full_text_lines))
        LogHelper.print()
        LogHelper.info(f"[查找 NER 实体] 已完成 ...")

        return words