import os
import re
import gc
import json
import warnings
import unicodedata
from types import SimpleNamespace
from typing import Generator

import torch
import onnxruntime
from lemminflect import getLemma
from transformers import pipeline
from transformers import AutoTokenizer
from transformers import AutoModelForTokenClassification
from optimum.onnxruntime import ORTModelForTokenClassification

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper
from helper.ProgressHelper import ProgressHelper

class NER:

    TASK_MODES = SimpleNamespace()
    TASK_MODES.QUICK = 10
    TASK_MODES.ACCURACY = 20

    GPU_BOOST = torch.cuda.is_available()
    BATCH_SIZE = 32 if GPU_BOOST else 1
    MODEL_PATH = "resource/kg_ner_gpu" if GPU_BOOST else "resource/kg_ner_cpu"

    RE_SPLIT_BY_PUNCTUATION = re.compile(
        r"[" +
        rf"{TextHelper.GENERAL_PUNCTUATION[0]}-{TextHelper.GENERAL_PUNCTUATION[1]}" +
        rf"{TextHelper.CJK_SYMBOLS_AND_PUNCTUATION[0]}-{TextHelper.CJK_SYMBOLS_AND_PUNCTUATION[1]}" +
        rf"{TextHelper.HALFWIDTH_AND_FULLWIDTH_FORMS[0]}-{TextHelper.HALFWIDTH_AND_FULLWIDTH_FORMS[1]}" +
        rf"{TextHelper.LATIN_PUNCTUATION_BASIC_1[0]}-{TextHelper.LATIN_PUNCTUATION_BASIC_1[1]}" +
        rf"{TextHelper.LATIN_PUNCTUATION_BASIC_2[0]}-{TextHelper.LATIN_PUNCTUATION_BASIC_2[1]}" +
        rf"{TextHelper.LATIN_PUNCTUATION_BASIC_3[0]}-{TextHelper.LATIN_PUNCTUATION_BASIC_3[1]}" +
        rf"{TextHelper.LATIN_PUNCTUATION_BASIC_4[0]}-{TextHelper.LATIN_PUNCTUATION_BASIC_4[1]}" +
        rf"{TextHelper.LATIN_PUNCTUATION_GENERAL[0]}-{TextHelper.LATIN_PUNCTUATION_GENERAL[1]}" +
        rf"{TextHelper.LATIN_PUNCTUATION_SUPPLEMENTAL[0]}-{TextHelper.LATIN_PUNCTUATION_SUPPLEMENTAL[1]}" +
        r"·・♥]+"
    )

    NER_TYPES = {
        "PER": "PER",       # 表示人名，如"张三"、"约翰·多伊"等。
        "ORG": "ORG",       # 表示组织，如"联合国"、"苹果公司"等。
        "LOC": "LOC",       # 表示地点，通常指非地理政治实体的地点，如"房间"、"街道"等。
        "PRD": "PRD",       # 表示产品，如"iPhone"、"Windows操作系统"等。
        "EVT": "EVT",       # 表示事件，如"奥运会"、"地震"等。
    }

    LANGUAGE = SimpleNamespace()
    LANGUAGE.ZH = 100
    LANGUAGE.EN = 200
    LANGUAGE.JP = 300
    LANGUAGE.KO = 400

    def __init__(self) -> None:
        # 忽略指定的警告信息
        warnings.filterwarnings(
            "ignore",
            message = "1Torch was not compiled with flash attention",
            category = UserWarning,
        )

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
            aggregation_strategy = "simple",
        )

    # 释放资源
    def release(self) -> None:
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

    # 生成器
    def generator(self, chunks: list) -> Generator:
        for chunk in chunks:
            yield chunk

    # 加载黑名单文件内容
    def load_blacklist(self) -> None:
        self.blacklist = set()

        try:
            for entry in os.scandir("blacklist"):
                if entry.is_file() and entry.name.endswith(".json"):
                    with open(entry.path, "r", encoding = "utf-8") as reader:
                        for v in json.load(reader):
                            if v.get("srt") != None:
                                self.blacklist.add(v.get("srt"))
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 判断是否是有意义的汉字词语
    def is_valid_cjk_word(self, surface: str, blacklist: set) -> bool:
        flag = True

        if len(surface) <= 1:
            return False

        if surface in blacklist:
            return False

        if not TextHelper.has_any_cjk(surface):
            return False

        return flag

    # 判断是否是有意义的英文词语
    def is_valid_english_word(self, surface: str, blacklist: set, ner_type: str, unique_words: set[str]) -> bool:
        flag = True

        if len(surface) <= 2:
            return False

        if surface.lower() in blacklist:
            return False

        if not TextHelper.has_any_latin(surface):
            return False

        # 排除类型为角色首字母没有大写的词语
        if ner_type == "PER" and not surface[0].isupper():
            return False

        # 排除不是完整单词的词语
        if unique_words != None:
            chunks = re.findall(r"\b\w+\b", surface)
            if len(chunks) > 0 and not all(chunk in unique_words for chunk in chunks):
                return False

        return flag

    # 判断是否是有意义的日文词语
    def is_valid_japanese_word(self, surface: str, blacklist: set) -> bool:
        flag = True

        if len(surface) <= 1:
            return False

        if surface in blacklist:
            return False

        if not TextHelper.has_any_japanese(surface):
            return False

        return flag

    # 判断是否是有意义的韩文词语
    def is_valid_korean_word(self, surface: str, blacklist: set) -> bool:
        flag = True

        if len(surface) <= 1:
            return False

        if surface in blacklist:
            return False

        if not TextHelper.has_any_korean(surface):
            return False

        return flag

    # 生成片段
    def generate_chunks(self, input_lines: list, chunk_size: int) -> list[str]:
        chunks = []

        chunk = ""
        chunk_length = 0
        for line in input_lines:
            encoding = self.tokenizer(
                line,
                padding = False,
                truncation = True,
                max_length = chunk_size - 3,
            )
            length = len(encoding.input_ids)

            if chunk_length + length > chunk_size - 3:
                chunks.append(chunk)
                chunk = ""
                chunk_length = 0

            chunk = chunk + "\n" + line
            chunk_length = chunk_length + length + 1

        # 循环结束后添加最后一段
        if len(chunk) > 0:
            chunks.append(chunk)

        return chunks

    # 生成词语
    def generate_words(self, text: str, line: str, score: float, ner_type: str, language: int, unique_words: set[str]) -> list[Word]:
        words = []

        if ner_type != "PER":
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
                if not self.is_valid_english_word(surface, self.blacklist, ner_type, unique_words):
                    continue

            # 日文词语判断
            if language == NER.LANGUAGE.JP:
                surface = TextHelper.strip_not_japanese(surface).strip("の")
                if not self.is_valid_japanese_word(surface, self.blacklist):
                    continue

            # 韩文词语判断
            if language == NER.LANGUAGE.KO:
                surface = TextHelper.strip_not_korean(surface)
                if not self.is_valid_korean_word(surface, self.blacklist):
                    continue

            word = Word()
            word.count = 1
            word.score = score
            word.surface = surface
            word.ner_type = ner_type
            word.context.append(line)
            words.append(word)

        return words

    # 获取英语词根
    def get_english_lemma(self, surface: str) -> str:
        lemma_noun = getLemma(surface, upos = "NOUN")[0]
        lemma_propn = getLemma(surface, upos = "PROPN")[0]

        if lemma_propn != surface:
            return lemma_propn
        elif lemma_noun != surface:
            return lemma_noun
        else:
            return surface

    # 计算字符串的实际显示长度
    def get_display_lenght(self, text: str) -> int:
        # unicodedata.east_asian_width(c) 返回字符 c 的东亚洲宽度属性。
        # NaH 表示窄（Narrow）、中立（Neutral）和半宽（Halfwidth）字符，这些字符通常被认为是半角字符。
        # 其他字符（如全宽字符）的宽度属性为 W 或 F，这些字符被认为是全角字符。
        return sum(1 if unicodedata.east_asian_width(c) in "NaH" else 2 for c in text)

    # 查找 Token 所在的行
    def get_line_by_offset(self, text: str, lines: list[str], offsets: list[tuple[int]], start: int, end: int) -> str:
        result = ""

        # 当实体词语位于行的末尾时，会将换行符的长度也计入起止位置，所以要 end 要 -1
        if text != "" and text[-1] == " ":
            end = end - 1

        for line, offset in zip(lines, offsets):
            if start >= offset[0] and end <= offset[1]:
                result = line
                break

        return result

    # 查找 NER 实体
    def search_for_entity(self, input_lines: list[str], input_names: list[str], language: int) -> list[Word]:
        words = []

        if self.GPU_BOOST:
            LogHelper.info("检测到有效的 [green]GPU[/] 环境，已启用 [green]GPU[/] 加速 ...")
        else:
            LogHelper.warning("未检测到有效的 [green]GPU[/] 环境，无法启用 [green]GPU[/] 加速 ...")

        LogHelper.print("")
        with LogHelper.status("正在对文本进行预处理 ..."):
            chunks = self.generate_chunks(input_lines, 512)

        with ProgressHelper.get_progress() as progress:
            pid = progress.add_task("查找 NER 实体", total = None)

            i = 0
            unique_words = None
            for result in self.classifier(self.generator(chunks),batch_size = self.BATCH_SIZE):
                # 获取当前文本
                chunk = chunks[i]

                # 计算各行的起止位置
                chunk_lines = chunk.splitlines()
                chunk_offsets = []
                for line in chunk_lines:
                    if len(chunk_offsets) == 0:
                        start = 0
                    else:
                        start = chunk_offsets[-1][1]

                    chunk_offsets.append((start, start + len(line) + 1)) # 字符数加上换行符的长度

                # 如果是英文，则抓取去重词表，再计算并添加所有词根到词表，以供后续筛选词语
                if language == NER.LANGUAGE.EN:
                    unique_words = set(re.findall(r"\b\w+\b", chunk))
                    unique_words.update(set(self.get_english_lemma(v) for v in unique_words))

                # 处理 NER模型 识别结果
                for token in result:
                    text = token.get("word")
                    line = self.get_line_by_offset(text, chunk_lines, chunk_offsets, token.get("start"), token.get("end"))
                    score = token.get("score")
                    entity_group = token.get("entity_group")
                    words.extend(self.generate_words(text, line, score, entity_group, language, unique_words))

                i = i + 1
                progress.update(pid, advance = 1, total = len(chunks))

        # 后处理步骤
        with LogHelper.status("正在对文本进行后处理 ..."):
            # 添加输入文件中读取到的角色名
            for name, line in input_names:
                words.extend(self.generate_words(name, line, 65535, "PER", language, None))

            # 匹配【】中的字符串
            seen = set()
            for line in input_lines:
                for name in re.findall(r"【(.*?)】", line):
                    if self.get_display_lenght(name) <= 16:
                        for word in self.generate_words(name, line, 65535, "PER", language, None):
                            seen.add(word.surface) if word.surface not in seen else None
                            words.append(word)

        # 打印通过模式匹配抓取的角色实体
        LogHelper.print("")
        LogHelper.info(f"[查找 NER 实体] 已完成 ...")
        LogHelper.info(f"[查找 NER 实体] 通过模式 [green]【(.*?)】[/] 抓取到角色实体 - {", ".join(seen)}") if len(seen) > 0 else None

        # 释放显存
        self.release()
        return words

    # 通过 词语形态 校验词语
    def lemmatize_words_by_morphology(self, words: list[Word]) -> list[Word]:
        seen = set()
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
                    word_ex.surface = v
                    word_ex.count = word.count
                    word_ex.score = word.score
                    word_ex.context = word.context
                    word_ex.ner_type = word.ner_type

                    roots.append(v)
                    words_ex.append(word_ex)

            if len(roots) > 0:
                key = (word.ner_type, word.surface)

                if key not in seen:
                    LogHelper.info(f"通过 [green]词语形态[/] 还原词根 - {word.ner_type} - {word.surface} [green]->[/] {" / ".join(roots)}")

                seen.add(key)
                word.ner_type = ""

        # 合并拆分出来的词语
        words.extend(words_ex)
        return words