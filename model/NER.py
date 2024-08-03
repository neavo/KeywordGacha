import re
import os
import json

import torch
import onnxruntime

from sudachipy import tokenizer
from sudachipy import dictionary
from transformers import pipeline as transformers_pipeline
from transformers import AutoTokenizer
from transformers import AutoModelForTokenClassification
from optimum.pipelines import pipeline as onnx_pipeline
from optimum.onnxruntime import ORTModelForTokenClassification

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper
from helper.ProgressHelper import ProgressHelper

class NER:

    TASK_MODES = type("GClass", (), {})()
    TASK_MODES.QUICK = 10
    TASK_MODES.ACCURACY = 20

    MODEL_PATH_CPU= "resource\\kg_ner_ja_onnx_cpu"
    MODEL_PATH_GPU = "resource\\globis_university_deberta_v3_japanese_xsmall_best"
    LINE_SIZE_PER_GROUP = 256

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
        "PER": "PER",       # 表示人名，如"张三"、"约翰·多伊"等。
        "ORG": "ORG",       # 表示组织，如"联合国"、"苹果公司"等。
        "LOC": "LOC",       # 表示地点，通常指非地理政治实体的地点，如"房间"、"街道"等。
        "INS": "INS",       # 表示设施，如"医院"、"学校"、"机场"等。
        "PRD": "PRD",       # 表示产品，如"iPhone"、"Windows操作系统"等。
        "EVT": "EVT",       # 表示事件，如"奥运会"、"地震"等。

        "人名": "PER",
        "法人名": "ORG",
        "政治的組織名": "ORG",
        "その他の組織名": "ORG",
        "地名": "LOC",
        "施設名": "INS",
        "製品名": "PRD",
        "イベント名": "EVT",
    }

    def __init__(self):
        self.blacklist = ""
        self.sudachipy_tokenizer = dictionary.Dictionary(dict_type = "full").create(tokenizer.Tokenizer.SplitMode.C)

        # 在支持的设备和模型上启用 GPU 加速
        if torch.cuda.is_available() and LogHelper.is_debug():
            model = AutoModelForTokenClassification.from_pretrained(
                self.MODEL_PATH_GPU,
                torch_dtype = torch.float16,
                local_files_only = True,
            )

            self.classifier = transformers_pipeline(
                "token-classification",
                model = model,
                tokenizer = AutoTokenizer.from_pretrained(
                    self.MODEL_PATH_GPU,
                    truncation = True,
                    max_length = 512,
                    model_max_length = 512,
                    local_files_only = True,
                ),
                device = "cuda",
                batch_size = 256,
                aggregation_strategy = "simple",
            )
        else:
            self.classifier = onnx_pipeline(
                "token-classification",
                model = ORTModelForTokenClassification.from_pretrained(
                    self.MODEL_PATH_CPU,
                    local_files_only = True,
                ),
                tokenizer = AutoTokenizer.from_pretrained(
                    self.MODEL_PATH_CPU,
                    truncation = True,
                    max_length = 512,
                    model_max_length = 512,
                    local_files_only = True,
                ),
                device = "cpu",
                batch_size = min(8, os.cpu_count()),
                aggregation_strategy = "simple", 
            )

    # 从指定路径加载黑名单文件内容
    def load_blacklist(self, filepath):
        try:
            with open(filepath, "r", encoding = "utf-8") as file:
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

        # 过滤非实体
        if ner_type not in self.NER_TYPES:
            return []

        words = [Word()]
        words[0] = Word()
        words[0].count = 1
        words[0].score = score
        words[0].surface = surface
        words[0].ner_type = ner_type

        return words

    # 查找 NER 实体
    def search_for_entity(self, full_lines):
        words = []
        full_lines_chunked = [
            full_lines[i : i + self.LINE_SIZE_PER_GROUP]
            for i in range(0, len(full_lines), self.LINE_SIZE_PER_GROUP)
        ]

        LogHelper.print()
        with ProgressHelper.get_progress() as progress:
            pid = progress.add_task("查找 NER 实体", total = None)

            for k, lines in enumerate(full_lines_chunked):
                self.classifier.call_count = 0 # 防止出现应使用 dateset 的提示
                for i, doc in enumerate(self.classifier(lines)):
                    for token in doc:
                        surfaces = re.split(self.RE_SPLIT_BY_PUNCTUATION, token.get("word").replace(" ", ""))
                        for surface in surfaces:
                            score = token.get("score")
                            entity_group = self.NER_TYPES.get(token.get("entity_group"), "")
                            words.extend(self.generate_words(score, surface, entity_group))

                progress.update(pid, advance = 1, total = len(full_lines_chunked))

        with LogHelper.status(f"正在查找 NER 实体 ..."):
            pid = progress.add_task("查找 NER 实体", total = None)

            for k, lines in enumerate(full_lines_chunked):
                tokens = self.sudachipy_tokenizer.tokenize("".join(lines))
                for token in tokens:
                    if "人名" in token.part_of_speech():
                        surfaces = re.split(self.RE_SPLIT_BY_PUNCTUATION, token.surface().replace(" ", ""))
                        for surface in surfaces:
                            score = 1.0
                            entity_group = self.NER_TYPES.get("PER")
                            words.extend(self.generate_words(score, surface, entity_group))

        LogHelper.print()
        LogHelper.info(f"[查找 NER 实体] 已完成 ...")

        return words

    # 通过 出现次数 还原词根
    def lemmatize_words_by_count(self, words, full_lines):
        words_map = {}
        for word in words:
            key = tuple(word.context)

            if key not in words_map:
                words_map[key] = word
                continue
            else:
                ex_word = words_map[key]

            if word.count != ex_word.count and abs(word.count - ex_word.count) / max(word.count, ex_word.count, 1) > 0.05:
                continue

            if  (word.surface in ex_word.surface or ex_word.surface in word.surface) and word.surface != ex_word.surface:
                LogHelper.info(f"通过 [green]出现次数[/] 还原词根 - {word.ner_type} - {word.surface}, {ex_word.surface}")
                words_map[key] = word if len(word.surface) > len(ex_word.surface) else ex_word

        # 根据 word_map 更新words
        updated_words = []
        for word in words:
            updated_words.append(words_map[tuple(word.context)])

        # 更新上下文
        for word in updated_words:
            word.set_context(word.surface, full_lines)

        return updated_words

    # 获取 CJK Token 的数量 
    def number_of_cjk_tokens(self, tokens):
        return len([token for token in tokens if TextHelper.is_all_cjk(token.surface())])

    # 获取词根 
    def get_root_from_tokens(self, tokens):
        root = ""
        tokens_noun = [token for token in tokens if any("名詞" == v for v in token.part_of_speech())]
        tokens_noun.sort(key = lambda v: -len(v.surface()))

        # 如果只有一个名词词根，取第一个
        if len(tokens_noun) == 1:
            if TextHelper.is_valid_japanese_word(tokens_noun[0].surface(), self.blacklist):
                return tokens_noun[0].surface()
        else:
            surface_0 = tokens_noun[0].surface()
            surface_1 = tokens_noun[1].surface()

            # 最长的两个词根，如果一个是汉字词，另一个不是汉字词，取不是的
            if not TextHelper.is_all_cjk(surface_0) and TextHelper.is_all_cjk(surface_1):
                if TextHelper.is_valid_japanese_word(surface_0, self.blacklist):
                    return surface_0
            if TextHelper.is_all_cjk(surface_0) and not TextHelper.is_all_cjk(surface_1):
                if TextHelper.is_valid_japanese_word(surface_1, self.blacklist):
                    return surface_1

            # 最长的两个词根，如果长度不一样，取长的
            if len(surface_0) > len(surface_1):
                if TextHelper.is_valid_japanese_word(surface_0, self.blacklist):
                    return surface_0
            if len(surface_0) < len(surface_1):
                if TextHelper.is_valid_japanese_word(surface_1, self.blacklist):
                    return surface_1

        # 如果全部规则都没有命中，返回空字符串
        # LogHelper.debug(f"{tokens_noun}")
        return root

    # 通过 词语形态学 校验词语
    def validate_words_by_morphology(self, words, full_lines):
        for word in words:
            tokens = self.sudachipy_tokenizer.tokenize(word.surface)
            tokens_noun = [token for token in tokens if any("名詞" == v for v in token.part_of_speech())]

            # 如果没有任何名词成分，剔除
            if len(tokens_noun) == 0:
                LogHelper.info(f"通过 [green]词语形态学[/] 剔除词语 - {word.ner_type} - {word.surface}")
                word.ner_type = ""
                continue

        for word in words:
            tokens = self.sudachipy_tokenizer.tokenize(word.surface)

            # 以下步骤只对角色实体进行
            if not word.ner_type == self.NER_TYPES.get("PER"):
                continue

            # 如果已不能再拆分，跳过
            if len(tokens) <= 1:
                continue

            # 前面的步骤中已经移除了首尾的 の，如果还有，那就是 AのB 的形式，跳过
            if "の" in word.surface:
                continue

            # 如果有超过一个 CJK Token，说明是汉字复合词，易误判，跳过
            if self.number_of_cjk_tokens(tokens) > 1:
                continue

            # 获取词根，获取成功则更新词语
            root = self.get_root_from_tokens(tokens)
            if root != "":
                LogHelper.info(f"通过 [green]词语形态学[/] 还原词根 - {word.ner_type} - {word.surface} [green]->[/] {root}")
                word.surface = root
                word.set_context(word.surface, full_lines)

        return words

    # 通过 重复性 校验词语
    def validate_words_by_duplication(self, words):
        person_set = set(word.surface for word in words if word.ner_type == "PER")

        for word in words:
            if word.ner_type == "PER":
                continue

            if any(v in word.surface for v in person_set):
                LogHelper.info(f"通过 [green]重复性校验[/] 剔除词语 - {word.ner_type} - {word.surface}")
                word.ner_type = ""

        return words