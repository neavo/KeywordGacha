import re
import os
import json

import spacy
from optimum.pipelines import pipeline

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper
from helper.ProgressHelper import ProgressHelper

class NER:

    TASK_MODES = type("GClass", (), {})()
    TASK_MODES.QUICK = 10
    TASK_MODES.ACCURACY = 20

    ONNX_PATH = "resource\\kg_ner_ja_onnx_avx512"
    ONNX_BACTH_SIZE = 8
    ONNX_SIZE_PER_GROUP = 256

    SPACY_N_PROCESS = 4
    SPACY_BACTH_SIZE = 128

    NER_TYPES = [
        # "",               # 表示非实体，数量极多
        # "CARDINAL",       # 表示基数词，如数字"1"、"三"等。
        # "DATE",           # 表示日期，如"2024年07月11日"。
        # "EVENT",          # 表示事件，如"奥运会"、"地震"等。
        # "FAC",            # 表示设施，如"医院"、"学校"、"机场"等。
        # "GPE",            # 表示地理政治实体，如"中国"、"纽约"等。
        # "LANGUAGE",       # 表示语言，如"英语"、"汉语"等。
        # "LAW",            # 表示法律、法规，如"宪法"、"民法典"等。
        # "LOC",            # 表示地点，通常指非地理政治实体的地点，如"房间"、"街道"等。
        # "MONEY",          # 表示货币，如"100美元"、"500欧元"等。
        # "MOVEMENT",       # 表示运动或趋势，如"女权运动"、"环保运动"等。
        # "NORP",           # 表示民族或宗教组织，如"基督教"、"伊斯兰教"等。
        # "ORDINAL",        # 表示序数词，如"第一"、"第二"等。
        # "ORG",            # 表示组织，如"联合国"、"苹果公司"等。
        # "PERCENT",        # 表示百分比，如"50%"。
        "PERSON",           # 表示人名，如"张三"、"约翰·多伊"等。
        "PET_NAME",         # 表示宠物的名字，如"小白"、"Max"等。
        # "PHONE",          # 表示电话号码，如"123-456-7890"。
        # "PRODUCT",        # 表示产品，如"iPhone"、"Windows操作系统"等。
        # "QUANTITY",       # 表示数量，如"两公斤"、"三个"等。
        # "TIME",           # 表示时间，如"下午三点"、"午夜"等。
        # "TITLE_AFFIX",    # 表示头衔或后缀，如"博士"、"先生"、"女士"等。
        # "WORK_OF_ART",    # 表示艺术作品，如"蒙娜丽莎"、"悲惨世界"等。
    ]

    ONNX_TO_SAPCY = {
        "O": "",            # 表示非实体，数量极多
        "PER": "PERSON",    # 表示人名，如"张三"、"约翰·多伊"等。
        "ORG": "ORG",       # 表示组织，如"联合国"、"苹果公司"等。
        "P": "ORG",         # 表示组织，如"联合国"、"苹果公司"等。
        "O": "ORG",         # 表示组织，如"联合国"、"苹果公司"等。
        "ORG-P": "ORG",     # 似乎是文档写错了，猜测： P = ORG-P
        "ORG-O": "ORG",     # 似乎是文档写错了，猜测： O = ORG-O
        "LOC": "LOC",       # 表示地点，通常指非地理政治实体的地点，如"房间"、"街道"等。
        "INS": "FAC",       # 表示设施，如"医院"、"学校"、"机场"等。
        "PRD": "PRODUCT",   # 表示产品，如"iPhone"、"Windows操作系统"等。
        "EVT": "EVENT",     # 表示事件，如"奥运会"、"地震"等。
    }

    def __init__(self):
        self.blacklist = ""

        self.spacy_tokenizer = spacy.load(
            "resource\\kg_ner_ja",
            exclude = [
                "parser",
                "tok2vec",
                "morphologizer",
                "attribute_ruler"
            ]
        )

        self.onnx_tokenizer = pipeline(
            "token-classification",
            model = self.ONNX_PATH, 
            batch_size = max(os.cpu_count(), self.ONNX_BACTH_SIZE),
            aggregation_strategy = "simple", 
            accelerator = "ort"
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

    # 添加词语 
    def add_to_words(self, words, score, surface, ner_type):
        word = Word()
        word.count = 1
        word.score = score
        word.surface = surface
        word.ner_type = ner_type

        # 判断评分
        if word.score < 0.80:
            return words

        # 判断词性
        if not word.ner_type in self.NER_TYPES:
            return words

        # 有效性检查
        if not TextHelper.is_valid_japanese_word(word.surface, self.blacklist):
            return words

        words.append(word)
        return words

    # 查找 NER 实体 
    def search_for_entity_qucik(self, full_text_lines):
        words = []

        LogHelper.print()
        with ProgressHelper.get_progress() as progress:
            pid = progress.add_task("查找 NER 实体", total = None)
            for doc in self.spacy_tokenizer.pipe(full_text_lines, n_process = self.SPACY_N_PROCESS, batch_size = self.SPACY_BACTH_SIZE):
                for token in doc:
                    text = token.text.strip("の")
                    text = TextHelper.strip_punctuation(text)
                    surfaces = re.split(r'[・ ]', text) # ・ 和 空格 都作为分隔符
                    
                    for surface in surfaces:
                        score = 1.0 # Spacy 分析结果中没有置信度，默认为可信
                        entity_group = token.ent_type_
                        words = self.add_to_words(words, score, surface, entity_group)

                progress.update(pid, advance = 1, total = len(full_text_lines))
        LogHelper.print()
        LogHelper.info(f"[查找 NER 实体] 已完成 ...")

        return words
        
    # 查找 NER 实体
    def search_for_entity_accuracy(self, full_text_lines):
        words = []
        full_text_lines = [
            full_text_lines[i : i + self.ONNX_SIZE_PER_GROUP]
            for i in range(0, len(full_text_lines), self.ONNX_SIZE_PER_GROUP)
        ]

        LogHelper.print()
        with ProgressHelper.get_progress() as progress:
            pid = progress.add_task("使用查找 NER 实体", total = None)

            for k, lines in enumerate(full_text_lines):
                for i, doc in enumerate(self.onnx_tokenizer(lines)):
                    for token in doc:
                        text = token.get("word").strip("の")
                        text = TextHelper.strip_punctuation(text)
                        surfaces = re.split(r'[・ ]', text) # ・ 和 空格 都作为分隔符

                        for surface in surfaces:
                            score = token.get("score")
                            entity_group = self.ONNX_TO_SAPCY[token.get("entity_group")]
                            words = self.add_to_words(words, score, surface, entity_group)

                progress.update(pid, advance = 1, total = len(full_text_lines))
        LogHelper.print()
        LogHelper.info(f"[查找 NER 实体] 已完成 ...")

        return words

    # 还原词根
    def lemmatize_words(self, words):
        # 通过分词器还原词根
        for word in words:
            if len(word.surface) < 3 and TextHelper.is_all_cjk(word.surface):
                continue

            surface = self.spacy_tokenizer(word.surface)[0].lemma_
            if TextHelper.is_valid_japanese_word(surface, self.blacklist):
                word.surface = surface

        # 通过上下文和次数还原词根
        word_map = {}
        for word in words:
            context_str = ','.join(word.context)
            key = (context_str, word.count)

            if key not in word_map:
                # 如果key不存在，直接添加到字典中
                word_map[key] = word
            else:
                # 检查并更新最长词根，选择最长的词根作为新的值
                existing_word = word_map[key]
                if word.surface in existing_word.surface or existing_word.surface in word.surface:
                    LogHelper.debug(f"通过上下文和次数还原词根 - {word.surface}, {existing_word.surface}")
                    word_map[key] = word if len(word.surface) > len(existing_word.surface) else existing_word

        # 根据 word_map 更新words
        updated_words = []
        for word in words:
            context_str = ','.join(word.context)
            key = (context_str, word.count)
            updated_words.append(word_map[key])

        return updated_words