import re
import os
import json

import torch
import onnxruntime

from sudachipy import tokenizer
from sudachipy import dictionary
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

    ONNX_PATH = "resource\\kg_ner_ja_onnx_gpu" if torch.cuda.is_available() else "resource\\kg_ner_ja_onnx_cpu"
    ONNX_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    ONNX_BACTH_SIZE = 256 if torch.cuda.is_available() else min(os.cpu_count(), 8)
    ONNX_SIZE_PER_GROUP = 512 if torch.cuda.is_available() else 256

    RE_SPLIT_BY_PUNCTUATION = re.compile(
        rf"[" +
        rf"{TextHelper.GENERAL_PUNCTUATION[0]}-{TextHelper.GENERAL_PUNCTUATION[1]}" +
        rf"{TextHelper.CJK_SYMBOLS_AND_PUNCTUATION[0]}-{TextHelper.CJK_SYMBOLS_AND_PUNCTUATION[1]}" +
        rf"{TextHelper.HALFWIDTH_AND_FULLWIDTH_FORMS[0]}-{TextHelper.HALFWIDTH_AND_FULLWIDTH_FORMS[1]}" +
        rf"{TextHelper.LATIN_PUNCTUATION_BASIC_1[0]}-{TextHelper.LATIN_PUNCTUATION_BASIC_1[1]}" +
        rf"{TextHelper.LATIN_PUNCTUATION_BASIC_2[0]}-{TextHelper.LATIN_PUNCTUATION_BASIC_2[1]}" +
        rf"{TextHelper.LATIN_PUNCTUATION_BASIC_3[0]}-{TextHelper.LATIN_PUNCTUATION_BASIC_3[1]}" +
        rf"{TextHelper.LATIN_PUNCTUATION_BASIC_4[0]}-{TextHelper.LATIN_PUNCTUATION_BASIC_4[1]}" +
        rf"{TextHelper.LATIN_PUNCTUATION_GENERAL[0]}-{TextHelper.LATIN_PUNCTUATION_GENERAL[1]}" +
        rf"{TextHelper.LATIN_PUNCTUATION_SUPPLEMENTAL[0]}-{TextHelper.LATIN_PUNCTUATION_SUPPLEMENTAL[1]}" +
        rf"・♥]+"
    )

    NER_TYPES = {
        "": "",                 # 表示非实体，数量极多
        "PERSON": "PERSON",     # 表示人名，如"张三"、"约翰·多伊"等。
        "ORG": "ORG",           # 表示组织，如"联合国"、"苹果公司"等。
        "LOC": "LOC",           # 表示地点，通常指非地理政治实体的地点，如"房间"、"街道"等。
        "INS": "INS",           # 表示设施，如"医院"、"学校"、"机场"等。
        "PRODUCT": "PRODUCT",   # 表示产品，如"iPhone"、"Windows操作系统"等。
        "EVENT": "EVENT",       # 表示事件，如"奥运会"、"地震"等。

        "人名": "PERSON",
        "法人名": "ORG",
        "政治的組織名": "ORG",
        "その他の組織名": "ORG",
        "地名": "LOC",
        "施設名": "INS",
        "製品名": "PRODUCT",
        "イベント名": "EVENT",
    }

    def __init__(self):
        self.blacklist = ""

        self.sudachipy_mode = tokenizer.Tokenizer.SplitMode.C
        self.sudachipy_tokenizer = dictionary.Dictionary().create()

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
                model_max_length = 512
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
                        surfaces = re.split(self.RE_SPLIT_BY_PUNCTUATION, token.get("word").replace(" ", "")) # ・ 和 空格 都作为分隔符
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

            if abs(word.count - ex_word.count) / max(word.count, ex_word.count, 1) > 0.05:
                continue

            if  (word.surface in ex_word.surface or ex_word.surface in word.surface) and word.surface != ex_word.surface:
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

            for token in self.sudachipy_tokenizer.tokenize("\n".join(word.context), self.sudachipy_mode):
                if word.surface in token.surface() and "名詞" not in token.part_of_speech():
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