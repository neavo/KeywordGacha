import os
import re
import gc
import json
import unicodedata
from typing import Generator

import torch
import onnxruntime
from optimum.onnxruntime import ORTModelForTokenClassification
from sudachipy import tokenizer
from sudachipy import dictionary
from transformers import pipeline
from transformers import AutoTokenizer
from transformers import PreTrainedModel
from transformers import AutoModelForTokenClassification
from transformers.utils import is_torch_bf16_gpu_available
from transformers.pipelines.base import Pipeline
from transformers.tokenization_utils_fast import PreTrainedTokenizerFast

from model.Word import Word
from module.LogHelper import LogHelper
from module.TextHelper import TextHelper
from module.ProgressHelper import ProgressHelper

class NER:

    # 语言模式
    class Language():

        ZH = 100
        EN = 200
        JA = 300
        KO = 400

    # 片段长度
    MAX_LENGTH = 512

    def __init__(self) -> None:
        super().__init__()

        # 初始化
        self.gpu_boost = torch.cuda.is_available()
        self.bacth_size = 32 if self.gpu_boost else 1
        self.model_path = "resource/kg_ner_gpu" if self.gpu_boost else "resource/kg_ner_cpu"

        self.model = self.load_model(self.model_path, self.gpu_boost)
        self.tokenizer = self.load_tokenizer(self.model_path)
        self.classifier = self.load_classifier(self.model, self.gpu_boost)

        self.sudachi = dictionary.Dictionary().create(tokenizer.Tokenizer.SplitMode.C)
        self.noun_set_cache = {}

    # 释放资源
    def release(self) -> None:
        LogHelper.debug(f"显存保留量 - {torch.cuda.memory_reserved()/1024/1024:>8.2f} MB")
        LogHelper.debug(f"显存分配量 - {torch.cuda.memory_allocated()/1024/1024:>8.2f} MB")

        del self.model
        del self.tokenizer
        del self.classifier

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

    # 加载模型
    def load_model(self, model_path: str, gpu_boost: bool) -> PreTrainedModel:
        if gpu_boost == True:
            return AutoModelForTokenClassification.from_pretrained(
                model_path,
                local_files_only = True,
                torch_dtype = torch.bfloat16 if is_torch_bf16_gpu_available() else torch.float16,
            ).to(device = "cuda")
        else:
            session_options = onnxruntime.SessionOptions()
            session_options.log_severity_level = 4
            return ORTModelForTokenClassification.from_pretrained(
                model_path,
                provider = "CPUExecutionProvider",
                session_options = session_options,
                use_io_binding = True,
                local_files_only = True,
            )

    # 加载分词器
    def load_tokenizer(self, model_path: str) -> PreTrainedTokenizerFast:
        return AutoTokenizer.from_pretrained(
            model_path,
            padding = "max_length",
            truncation = True,
            max_length = NER.MAX_LENGTH,
            model_max_length = NER.MAX_LENGTH,
            local_files_only = True,
        )

    # 加载分类器
    def load_classifier(self, model: PreTrainedModel, gpu_boost: bool) -> Pipeline:
        return pipeline(
            "token-classification",
            model = model,
            device = "cuda" if gpu_boost else "cpu",
            tokenizer = self.tokenizer,
            aggregation_strategy = "simple",
        )

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
    def generate_words(self, text: str, line: str, score: float, group: str, language: int, input_lines: list[str]) -> list[Word]:
        words = []

        # 生成名词表
        noun_set = self.generate_noun_set(line, language)

        # 生成词语列表
        # 当文本为英文且包含 ' 时不拆分，避免误拆复合短语
        # 当文本为中文时，使用包含空格的拆分规则
        # 否则使用不包含空格的拆分规则
        if language == NER.Language.EN and "'" in text:
            surfaces = [text]
        elif language in (NER.Language.ZH, NER.Language.JA):
            surfaces = [v.strip() for v in TextHelper.split_by_punctuation(text, True) if v.strip() != ""]
        else:
            surfaces = [v.strip() for v in TextHelper.split_by_punctuation(text, False) if v.strip() != ""]

        # 遍历词语
        for surface in surfaces:
            # 按语言移除首尾无效字符
            surface = self.strip_by_language(surface, language)

            # 跳过显示长度小于等于2的词语
            if self.get_display_lenght(surface) <= 2:
                continue

            # 按语言验证词语
            if self.verify_by_language(surface, language) == False:
                continue

            # 根据名词集合对词语进行修正
            surface = self.fix_by_noun_set(surface, line, noun_set, language)

            word = Word()
            word.count = 1
            word.score = score
            word.surface = surface
            word.group = group
            word.input_lines = input_lines
            word.context.append(line)
            words.append(word)
        return words

    # 生成名词集合
    def generate_noun_set(self, line: str, language: int) -> set[str]:
        # 优先从缓存中获取
        if line in self.noun_set_cache:
            return self.noun_set_cache[line]
        else:
            # 否则重新生成
            noun_set = set()

            # 语言为日语时
            if language == NER.Language.JA:
                # 获取名词集合
                for token in self.sudachi.tokenize(line):
                    # 获取表面形态
                    surface = token.surface()

                    # 跳过包含至少一个标点符号的条目
                    if TextHelper.has_any_punctuation(surface):
                        continue

                    # 跳过目标类型以外的条目
                    if not any(v in ",".join(token.part_of_speech()) for v in ("地名", "人名", "名詞")):
                        continue

                    noun_set.add(surface)

            # 语言为英语
            if language == NER.Language.EN:
                noun_set.update(re.findall(r"\b(.+?)\b", line))

            # 加入缓存并返回
            self.noun_set_cache[line] = noun_set
            return noun_set

    # 根据名词集合修正词语
    def fix_by_noun_set(self, text: str, line: str, noun_set: set[str], language: int) -> str:
        if language == NER.Language.JA:
            for noun in noun_set:
                if text == noun:
                    continue

                if text not in noun:
                    continue

                text = noun

        if language == NER.Language.EN:
            if text.count(" ") == 0:
                for noun in [v for v in noun_set if v.count(" ") == 0]:
                    if text == noun:
                        continue

                    if not (noun.startswith(text) or noun.endswith(text)):
                        continue

                    text = noun
            else:
                chunks = re.split(r" +", text)

                # 先修第一个词
                for noun in noun_set:
                    if chunks[1] == noun:
                        continue

                    if not noun.endswith(chunks[1]):
                        continue

                    if " ".join([noun] + chunks[1:]) not in line:
                        continue

                    chunks[-1] = noun

                # 在修最后一个词
                for noun in noun_set:
                    if chunks[-1] == noun:
                        continue

                    if not noun.startswith(chunks[-1]):
                        continue

                    if " ".join(chunks[:-1] + [noun]) not in line:
                        continue

                    chunks[-1] = noun

                # 将列表拼回去
                text = " ".join(chunks)

        return text

    # 按语言移除首尾无效字符
    def strip_by_language(self, text: str, language: int) -> str:
        if language == NER.Language.ZH:
            return TextHelper.strip_not_cjk(text).strip("的")

        if language == NER.Language.EN:
            return TextHelper.strip_not_latin(text).removeprefix("a ").removeprefix("an ").removeprefix("the ").strip()

        if language == NER.Language.JA:
            return TextHelper.strip_not_japanese(text).strip("の")

        if language == NER.Language.KO:
            return TextHelper.strip_not_korean(text)

    # 按语言进行验证
    def verify_by_language(self, text: str, language: int) -> bool:
        result = True

        if text.lower() in self.blacklist:
            result = False

        if language == NER.Language.ZH:
            if not TextHelper.has_any_cjk(text):
                result = False

        if language == NER.Language.EN:
            if not text[0].isupper():
                result = False

            if not TextHelper.has_any_latin(text):
                result = False

        if language == NER.Language.JA:
            if not TextHelper.has_any_japanese(text):
                result = False

        if language == NER.Language.KO:
            if not TextHelper.has_any_korean(text):
                result = False

        return result

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

    # 查找实体词语
    def search_for_entity(self, input_lines: list[str], language: int) -> list[Word]:
        words = []

        if self.gpu_boost:
            LogHelper.info("检测到有效的 [green]GPU[/] 环境，已启用 [green]GPU[/] 加速 ...")
        else:
            LogHelper.warning("未检测到有效的 [green]GPU[/] 环境，无法启用 [green]GPU[/] 加速 ...")

        LogHelper.print("")
        with LogHelper.status("正在对文本进行预处理 ..."):
            chunks = self.generate_chunks(input_lines, NER.MAX_LENGTH)

        with ProgressHelper.get_progress() as progress:
            pid = progress.add_task("查找实体词语", total = None)

            i = 0
            for result in self.classifier(self.generator(chunks), batch_size = self.bacth_size):
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

                # 处理 NER模型 识别结果
                for token in result:
                    text = token.get("word")
                    line = self.get_line_by_offset(text, chunk_lines, chunk_offsets, token.get("start"), token.get("end"))
                    score = token.get("score")
                    entity_group = token.get("entity_group")
                    words.extend(self.generate_words(text, line, score, entity_group, language, input_lines))

                i = i + 1
                progress.update(pid, advance = 1, total = len(chunks))

        # 匹配【】中的字符串
        seen = set()
        for line in input_lines:
            for name in re.findall(r"【(.*?)】", line):
                if self.get_display_lenght(name) <= 16:
                    for word in self.generate_words(name, line, 65535, "PER", language, input_lines):
                        seen.add(word.surface) if word.surface not in seen else None
                        words.append(word)

        # 打印通过模式匹配抓取的角色实体
        LogHelper.print("")
        LogHelper.info("[查找实体词语] 已完成 ...")
        LogHelper.info(f"[查找实体词语] 通过模式 [green]【(.*?)】[/] 抓取到角色实体 - {", ".join(seen)}") if len(seen) > 0 else None

        # 释放显存
        self.release()
        return words