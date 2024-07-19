import re
import os
import json

import spacy
import onnxruntime

from transformers import AutoTokenizer
from optimum.pipelines import pipeline
from optimum.onnxruntime import ORTModelForTokenClassification

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper
from helper.ProgressHelper import ProgressHelper

class NER:

    TASK_MODES = type("GClass", (), {})()
    TASK_MODES.QUICK = 10
    TASK_MODES.ACCURACY = 20

    ONNX_PATH = "resource\\kg_ner_ja_onnx_gpu" if LogHelper.is_debug() else "resource\\kg_ner_ja_onnx_cpu"
    ONNX_DEVICE = "cuda" if LogHelper.is_debug() else "cpu"
    ONNX_BACTH_SIZE = 256 if LogHelper.is_debug() else min(os.cpu_count(), 8)
    ONNX_SIZE_PER_GROUP = 512 if LogHelper.is_debug() else 256

    SPACY_PATH = "resource\\kg_ner_ja"
    SPACY_N_PROCESS = 2
    SPACY_BACTH_SIZE = 128

    NER_TYPES = {
        "": "",                 # 表示非实体，数量极多
        "PERSON": "PERSON",     # 表示人名，如"张三"、"约翰·多伊"等。
        "ORG": "ORG",           # 表示组织，如"联合国"、"苹果公司"等。
        "LOC": "LOC",           # 表示地点，通常指非地理政治实体的地点，如"房间"、"街道"等。
        "INS": "INS",           # 表示设施，如"医院"、"学校"、"机场"等。
        "PRODUCT": "PRODUCT",   # 表示产品，如"iPhone"、"Windows操作系统"等。
        "EVENT": "EVENT",       # 表示事件，如"奥运会"、"地震"等。
        "MISC": "MISC",         # 表示事件，如"奥运会"、"地震"等。

        "人名": "PERSON",
        "法人名": "ORG",
        "政治的組織名": "ORG",
        "その他の組織名": "ORG",
        "地名": "LOC",
        "施設名": "INS",
        "製品名": "PRODUCT",
        "イベント名": "EVENT",

        "O": "",                # 表示非实体，数量极多
        "PER": "PERSON",        # 表示人名，如"张三"、"约翰·多伊"等。
        "ORG": "ORG",           # 表示组织，如"联合国"、"苹果公司"等。
        "P": "ORG",             # 表示组织，如"联合国"、"苹果公司"等。
        "O": "ORG",             # 表示组织，如"联合国"、"苹果公司"等。
        "ORG-P": "ORG",         # 似乎是文档写错了，猜测： P = ORG-P
        "ORG-O": "ORG",         # 似乎是文档写错了，猜测： O = ORG-O
        "LOC": "LOC",           # 表示地点，通常指非地理政治实体的地点，如"房间"、"街道"等。
        "INS": "FAC",           # 表示设施，如"医院"、"学校"、"机场"等。
        "PRD": "PRODUCT",       # 表示产品，如"iPhone"、"Windows操作系统"等。
        "EVT": "EVENT",         # 表示事件，如"奥运会"、"地震"等。

        "CARDINAL": "MISC",     # 表示基数词，如数字"1"、"三"等。
        "DATE": "MISC",         # 表示日期，如"2024年07月11日"。
        "EVENT": "EVENT",       # 表示事件，如"奥运会"、"地震"等。
        "FAC": "FAC",           # 表示设施，如"医院"、"学校"、"机场"等。
        "GPE": "LOC",           # 表示地理政治实体，如"中国"、"纽约"等。
        "LANGUAGE": "MISC",     # 表示语言，如"英语"、"汉语"等。
        "LAW": "MISC",          # 表示法律、法规，如"宪法"、"民法典"等。
        "LOC": "LOC",           # 表示地点，通常指非地理政治实体的地点，如"房间"、"街道"等。
        "MONEY": "MISC",        # 表示货币，如"100美元"、"500欧元"等。
        "MOVEMENT": "ORG",      # 表示运动或趋势，如"女权运动"、"环保运动"等。
        "NORP": "ORG",          # 表示民族或宗教组织，如"基督教"、"伊斯兰教"等。
        "ORDINAL": "MISC",      # 表示序数词，如"第一"、"第二"等。
        "ORG": "ORG",           # 表示组织，如"联合国"、"苹果公司"等。
        "PERCENT": "MISC",      # 表示百分比，如"50%"。
        "PERSON": "PERSON",     # 表示人名，如"张三"、"约翰·多伊"等。
        "PET_NAME": "PERSON",   # 表示宠物的名字，如"小白"、"Max"等。
        "PHONE": "MISC",        # 表示电话号码，如"123-456-7890"。
        "PRODUCT": "PRODUCT",   # 表示产品，如"iPhone"、"Windows操作系统"等。
        "QUANTITY": "MISC",     # 表示数量，如"两公斤"、"三个"等。
        "TIME": "MISC",         # 表示时间，如"下午三点"、"午夜"等。
        "TITLE_AFFIX": "MISC",  # 表示头衔或后缀，如"博士"、"先生"、"女士"等。
        "WORK_OF_ART": "MISC",  # 表示艺术作品，如"蒙娜丽莎"、"悲惨世界"等。
    }

    def __init__(self):
        self.blacklist = ""

        self.spacy_tokenizer = spacy.load(
            self.SPACY_PATH,
            exclude = [
                # "parser",
                # "tok2vec",
                # "morphologizer",
                # "attribute_ruler"
            ]
        )

        session_options = onnxruntime.SessionOptions()
        session_options.log_severity_level = 4
        self.onnx_tokenizer = pipeline(
            "token-classification",
            model = ORTModelForTokenClassification.from_pretrained(
                self.ONNX_PATH,
                session_options = session_options,
                use_io_binding = True, 
                local_files_only = True,
            ),
            tokenizer = AutoTokenizer.from_pretrained(
                self.ONNX_PATH,
                padding = True,
                truncation = True,
                max_length = 512
            ),
            device = self.ONNX_DEVICE,
            batch_size = self.ONNX_BACTH_SIZE,
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

    # 生成词语 
    def generate_words(self, score, surface, ner_type):
        surface = TextHelper.strip_not_japanese(surface)
        surface = surface.strip("の")

        # 有效性检查
        if not TextHelper.is_valid_japanese_word(surface, self.blacklist):
            return []

        if ner_type == "" or ner_type == self.NER_TYPES.get("MISC"):
            return []

        words = [Word()]
        words[0] = Word()
        words[0].count = 1
        words[0].score = score
        words[0].surface = surface
        words[0].ner_type = ner_type

        return words

    # 查找 NER 实体 - 快速模式
    def search_for_entity_qucik(self, full_text_lines):
        words = []

        LogHelper.print()
        with ProgressHelper.get_progress() as progress:
            pid = progress.add_task("查找 NER 实体", total = None)
            for doc in self.spacy_tokenizer.pipe(full_text_lines, n_process = self.SPACY_N_PROCESS, batch_size = self.SPACY_BACTH_SIZE):
                for token in doc:
                    surfaces = re.split(r'[・]', token.text) # ・ 和 空格 都作为分隔符
                    for surface in surfaces:
                        # Spacy 结果中没有置信度参数，所以直接排除人名以外的条目
                        if (
                            self.NER_TYPES.get(token.ent_type_, "") == self.NER_TYPES.get("PERSON") 
                            or 
                            self.NER_TYPES.get(token.ent_type_, "") == self.NER_TYPES.get("PET_NAME")
                        ):
                            score = 1.0
                        else:
                            score = 0.0

                        entity_group = self.NER_TYPES.get(token.ent_type_, "")
                        words.extend(self.generate_words(score, surface, entity_group))

                progress.update(pid, advance = 1, total = len(full_text_lines))
        LogHelper.print()
        LogHelper.info(f"[查找 NER 实体] 已完成 ...")

        return words
        
    # 查找 NER 实体 - 精确模式
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
                self.onnx_tokenizer.call_count = 0 # 防止出现应使用 dateset 的提示
                for i, doc in enumerate(self.onnx_tokenizer(lines)):
                    for token in doc:
                        surfaces = re.split(r'[・ ]', token.get("word").replace(" ", "")) # ・ 和 空格 都作为分隔符
                        for surface in surfaces:
                            score = token.get("score")
                            entity_group = self.NER_TYPES.get(token.get("entity_group"), "")
                            words.extend(self.generate_words(score, surface, entity_group))

                progress.update(pid, advance = 1, total = len(full_text_lines))
        LogHelper.print()
        LogHelper.info(f"[查找 NER 实体] 已完成 ...")

        return words

    # 通过规则还原词根，如果词语为 假名 + 汉字 复合词，则移除末尾的汉字
    def lemmatize_words_by_rule(self, words):
        for word in words:
            if TextHelper.is_all_cjk(word.surface):
                continue

            # 判断是否是一个假名与汉字的混合词语 
            if not (
                TextHelper.has_any_cjk(word.surface)
                and 
                (TextHelper.has_any_hiragana(word.surface) or TextHelper.has_any_katakanae(word.surface))
            ):
                continue

            # 在前面的步骤中已经移除了首尾的 "の"，如还有，那就是 AAのBB 这种形式，应保留
            if "の" in word.surface:
                continue

            no_suffix = TextHelper.remove_suffix_cjk(word.surface)

            if len(no_suffix) == 1:
                continue

            LogHelper.info(f"通过 [green]规则还原[/] 还原词根 - {no_suffix}, {word.surface}")
            word.surface = no_suffix

        return words

    # 通过出现次数还原词根
    def lemmatize_words_by_count(self, words):
        words_map = {}
        for word in words:
            key = tuple(word.context)

            if key not in words_map:
                words_map[key] = word
                continue
            else:
                ex_word = words_map[key]

            if abs(word.count - ex_word.count) / max(word.count, ex_word.count) > 0.05:
                continue

            if word.surface in ex_word.surface or ex_word.surface in word.surface:
                LogHelper.info(f"通过 [green]出现次数[/] 还原词根 - {word.surface}, {ex_word.surface}")
                words_map[key] = word if len(word.surface) > len(ex_word.surface) else ex_word

        # 根据 word_map 更新words
        updated_words = []
        for word in words:
            updated_words.append(words_map[tuple(word.context)])

        return updated_words

    # 通过 词语形态学 校验词语
    def validate_words_by_morphology(self, words):
        for word in words:
            if len(word.context) == 0:
                continue

            doc = self.spacy_tokenizer("\n".join(word.context))
            for token in doc:
                if word.surface in token.text and "名詞" not in token.tag_:
                    LogHelper.info(f"通过 [green]词语形态学[/] 剔除词语 - {word.ner_type} - {word.surface}")
                    word.ner_type = ""
                    break

        return words

    # 通过 重复性 校验词语
    def validate_words_by_duplication(self, words):
        person_set = {word.surface for word in words if word.ner_type == "PERSON"}

        for word in words:
            if word.ner_type == "PERSON":
                continue

            if any(v in word.surface for v in person_set):
                LogHelper.info(f"通过 [green]重复性校验[/] 剔除词语 - {word.ner_type} - {word.surface}")
                word.ner_type = ""

        return words