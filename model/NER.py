import re
import gc
import os
import json

import torch
import onnxruntime
from transformers import pipeline
from transformers import AutoTokenizer
from transformers import AutoModelForTokenClassification
from optimum.onnxruntime import ORTModelForTokenClassification

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper
from helper.ProgressHelper import ProgressHelper

class NER:

    TASK_MODES = type("GClass", (), {})()
    TASK_MODES.QUICK = 10
    TASK_MODES.ACCURACY = 20

    GPU_BOOST = torch.cuda.is_available() and LogHelper.is_gpu_boost()
    MODEL_PATH = "resource\\kg_ner_ja_gpu" if GPU_BOOST else "resource\\kg_ner_ja_cpu"
    LINE_SIZE_PER_GROUP = 128

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
        "PRD": "PRD",       # 表示产品，如"iPhone"、"Windows操作系统"等。
        "EVT": "EVT",       # 表示事件，如"奥运会"、"地震"等。
    }

    LANGUAGE = type("GClass", (), {})()
    LANGUAGE.ZH = "ZH"
    LANGUAGE.EN = "EN"
    LANGUAGE.JP = "JP"

    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.MODEL_PATH,
            padding = "max_length",
            truncation = True,
            max_length = 512,
            model_max_length = 512,
            local_files_only = True,
        )

        if self.GPU_BOOST:
            self.model = AutoModelForTokenClassification.from_pretrained(
                self.MODEL_PATH,
                torch_dtype = torch.float16,
                local_files_only = True,
            ).to(device = "cuda")
        else:
            session_options = onnxruntime.SessionOptions()
            session_options.log_severity_level = 4
            self.model = ORTModelForTokenClassification.from_pretrained(
                self.MODEL_PATH, 
                provider = "CPUExecutionProvider",
                session_options = session_options,
                use_io_binding = True,
                local_files_only = True,
            )

        self.classifier = pipeline(
            "token-classification",
            model = self.model,
            device = "cuda" if self.GPU_BOOST else "cpu",
            tokenizer = self.tokenizer,
            batch_size = 64 if self.GPU_BOOST else min(10, os.cpu_count()),
            aggregation_strategy = "simple",
        )

    # 释放资源
    def release(self):
        LogHelper.debug(f"显存保留量 - {torch.cuda.memory_reserved()/1024/1024:>8.2f} MB")
        LogHelper.debug(f"显存分配量 - {torch.cuda.memory_allocated()/1024/1024:>8.2f} MB")

        if self.classifier:
            del self.classifier
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer

        gc.collect()
        torch.cuda.empty_cache()
        LogHelper.debug(f"显存保留量 - {torch.cuda.memory_reserved()/1024/1024:>8.2f} MB")
        LogHelper.debug(f"显存分配量 - {torch.cuda.memory_allocated()/1024/1024:>8.2f} MB")

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

    # 判断是否是有意义的汉字词语
    def is_valid_cjk_word(self, surface, blacklist):
        flag = True

        if len(surface) <= 1:
            return False

        if surface in blacklist:
            return False

        if not TextHelper.has_any_cjk(surface):
            return False

        return flag

    # 判断是否是有意义的英文词语
    def is_valid_english_word(self, surface, blacklist):
        flag = True

        if len(surface) <= 2:
            return False

        if surface in blacklist:
            return False

        if not TextHelper.has_any_latin(surface):
            return False

        return flag

    # 判断是否是有意义的日文词语
    def is_valid_japanese_word(self, surface, blacklist):
        flag = True

        if len(surface) <= 1:
            return False

        if surface in blacklist:
            return False

        if not TextHelper.has_any_japanese(surface):
            return False

        return flag

    # 生成词语 
    def generate_words(self, text, score, ner_type, language):
        words = []

        # 词语构成中存在空格的不拆分
        if language == NER.LANGUAGE.EN:
            surfaces = [text]
        else:
            surfaces = re.split(self.RE_SPLIT_BY_PUNCTUATION, text)

        for surface in surfaces:
            # 过滤非实体
            if ner_type not in self.NER_TYPES:
                continue

            # 中文词语判断
            if language == NER.LANGUAGE.ZH:
                surface = TextHelper.strip_not_cjk(surface)
                if not self.is_valid_cjk_word(surface, self.blacklist):
                    continue

            # 英文词语判断
            if language == NER.LANGUAGE.EN:
                surface = TextHelper.strip_not_latin(surface)
                if not self.is_valid_english_word(surface, self.blacklist):
                    continue

            # 日文词语判断
            if language == NER.LANGUAGE.JP:
                surface = TextHelper.strip_not_japanese(surface).strip("の")
                if not self.is_valid_japanese_word(surface, self.blacklist):
                    continue

            word = Word()
            word.count = 1
            word.score = score
            word.surface = surface
            word.ner_type = ner_type
            words.append(word)

        return words

    # 查找 NER 实体
    def search_for_entity(self, input_lines, input_names, language):
        words = []

        input_lines_chunked = [
            input_lines[i : i + self.LINE_SIZE_PER_GROUP]
            for i in range(0, len(input_lines), self.LINE_SIZE_PER_GROUP)
        ]

        if LogHelper.is_gpu_boost() and torch.cuda.is_available():
            LogHelper.info("启用 [green]GPU[/] 加速成功 ...")
        if LogHelper.is_gpu_boost() and not torch.cuda.is_available():
            LogHelper.warning("启用 [green]GPU[/] 加速失败 ...")

        LogHelper.print(f"")
        with ProgressHelper.get_progress() as progress:
            pid = progress.add_task("查找 NER 实体", total = None)   

            seen = set()
            for k, lines in enumerate(input_lines_chunked):
                self.classifier.call_count = 0 # 防止出现应使用 dateset 的提示

                # 使用 NER 模型抓取实体
                for i, doc in enumerate(self.classifier(lines)):
                    for token in doc:
                        text = token.get("word")
                        score = token.get("score")
                        entity_group = token.get("entity_group")
                        words.extend(self.generate_words(text, score, entity_group, language))
                
                # 匹配【】中的字符串
                for name in re.findall(r"【(.*?)】", "\n".join(lines)):
                    if len(name) <= 12:
                        text = name
                        score = 0.95
                        entity_group = "PER"

                        for word in self.generate_words(text, score, entity_group, language):
                            if word.surface in seen:
                                continue
                            else:
                                words.append(word)
                                seen.add(word.surface)                            

                # 进行英文和中文任务时显存保留量会暴涨，原因不明，暂时按照超过 2G 时手动释放显存进行处理
                torch.cuda.empty_cache() if torch.cuda.memory_reserved() > 2 * 1024 * 1024 * 1024 else None
                progress.update(pid, advance = 1, total = len(input_lines_chunked))

        # 打印通过模式匹配抓取的角色实体
        LogHelper.print()
        LogHelper.info(f"[查找 NER 实体] 已完成 ...")
        if len(seen) > 0:
            LogHelper.info(f"[查找 NER 实体] 通过模式 [green]【(.*?)】[/] 抓取到角色实体 - {", ".join(seen)}")        

        # 添加输入文件中读取到的角色名
        for name in input_names:
            surfaces = re.split(self.RE_SPLIT_BY_PUNCTUATION, name)
            for surface in surfaces:
                words.extend(self.generate_words(0.95, surface, "PER"))

        self.release()
        return words

    # 通过 词语形态 校验词语
    def lemmatize_words_by_morphology(self, words, full_lines):
        words_ex = []
        for word in words:
            # 以下步骤只对角色实体进行
            if not word.ner_type == "PER":
                continue

            # 前面的步骤中已经移除了首尾的 の，如果还有，那就是 AのB 的形式，跳过
            if "の" in word.surface:
                continue

            # 如果开头结尾都是汉字，跳过
            if TextHelper.is_cjk(word.surface[0]) and TextHelper.is_cjk(word.surface[-1]):
                continue

            # 拆分词根
            tokens = TextHelper.extract_japanese(word.surface)

            # 如果已不能再拆分，跳过
            if len(tokens) == 1:
                continue
          
            # 获取词根，获取成功则更新词语
            roots = []
            for k, v in enumerate(tokens):
                if self.is_valid_japanese_word(v, self.blacklist):
                    word_ex = Word()
                    word_ex.count = word.count
                    word_ex.score = word.score
                    word_ex.surface = v
                    word_ex.context = word_ex.search_context(full_lines)
                    word_ex.ner_type = word.ner_type

                    roots.append(v)
                    words_ex.append(word_ex)

            if len(roots) > 0:
                LogHelper.info(f"通过 [green]词语形态[/] 还原词根 - {word.ner_type} - {word.surface} [green]->[/] {" / ".join(roots)}")               
                word.ner_type = ""

        # 合并拆分出来的词语
        words.extend(words_ex)
        return words

    # 通过 出现次数 还原词根
    def lemmatize_words_by_count(self, words, full_lines):
        words_map = {}
        for word in words:
            key = (word.ner_type, "".join(word.context))

            if key not in words_map:
                words_map[key] = word
                continue
            else:
                ex_word = words_map[key]

            if word.count != ex_word.count and abs(word.count - ex_word.count) / max(word.count, ex_word.count, 1) > 0.05:
                continue

            if (word.surface in ex_word.surface or ex_word.surface in word.surface) and word.surface != ex_word.surface:
                if len(word.surface) > len(ex_word.surface):
                    LogHelper.info(f"通过 [green]出现次数[/] 还原词根 - {word.ner_type} - {ex_word.surface} [green]->[/] {word.surface}")
                    words_map[key] = word
                else:
                    LogHelper.info(f"通过 [green]出现次数[/] 还原词根 - {word.ner_type} - {word.surface} [green]->[/] {ex_word.surface}")
                    words_map[key] = ex_word

        # 根据 word_map 更新 words
        updated_words = []
        for word in words:
            updated_words.append(words_map[(word.ner_type, "".join(word.context))])

        # 更新上下文
        for word in updated_words:
            word.context = word.search_context(full_lines)

        return updated_words

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