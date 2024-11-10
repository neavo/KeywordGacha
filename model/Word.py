import threading
from dataclasses import field
from dataclasses import dataclass

import tiktoken
from helper.LogHelper import LogHelper

@dataclass
class Word:

    score: float = 0.0
    count: int = 0
    context: list[str] = field(default_factory = list)
    context_summary: str = ""
    context_translation: list[str] = field(default_factory = list)
    surface: str = ""
    surface_romaji: str = ""
    surface_translation: str = ""
    surface_translation_description: str = ""
    ner_type: str = ""
    attribute: str = ""
    llmresponse_summarize_context: str = ""
    llmresponse_translate_context: str = ""
    llmresponse_translate_surface: str = ""

    def __post_init__(self):
        pass

    # 获取token数量，优先从缓存中获取
    def get_token_count(self, line: str):
        if not hasattr(Word, "cache"):
            Word.cache = {}

        if not hasattr(Word, "cache_lock"):
            Word.cache_lock = threading.Lock()

        if not hasattr(Word, "tiktoken_encoding"):
            Word.tiktoken_encoding = tiktoken.get_encoding("cl100k_base")

        # 优先从缓存中取数据
        count = 0
        with Word.cache_lock:
            if line in Word.cache:
                count = Word.cache[line]
            else:
                count = len(Word.tiktoken_encoding.encode(line))
                Word.cache[line] = count
        return count

    # 按长度截取上下文并返回，如果句子长度全部超过 Token 阈值，则取最接近阈值的一条
    def clip_context(self, line_threshold: int, token_threshold: int):
        # 理论上不应该有上下文为空的情况
        if len(self.context) == 0:
            LogHelper.debug(f"len(self.context) == 0 : {self}")
            return []

        context = []
        context_token_count = 0

        for line in self.context:
            # 行数阈值有效，且超过行数阈值，则跳出循环
            if line_threshold > 0 and len(context) > line_threshold:
                break

            line_token_count = self.get_token_count(line)

            # 跳过超出阈值的句子
            if line_token_count > token_threshold:
                continue

            # 更新上下文与计数
            context.append(line)
            context_token_count = context_token_count + line_token_count

            # 如果计数超过 Token 阈值，则跳出循环
            if context_token_count > token_threshold:
                break

        # 如果句子长度全部超过 Token 阈值，则取最接近阈值的一条
        if len(context) == 0:
            context.append(
                min(
                    self.context,
                    key = lambda line: abs(self.get_token_count(line) - token_threshold)
                )
            )

        return context

    # 获取用于上下文分析任务的上下文文本
    def get_context_str_for_summarize(self):
        return "\n".join(self.clip_context(
            line_threshold = 0,
            token_threshold = 1536,
        )).replace("\n\n", "\n").strip()

    # 获取用于上下文翻译任务的上下文文本
    def get_context_str_for_translate(self):
        return "\n".join(self.clip_context(
            line_threshold = 16,
            token_threshold = 1024,
        )).replace("\n\n", "\n").strip()

    # 获取用于词语翻译任务的上下文文本
    def get_context_str_for_surface_translate(self):
        return "\n".join(self.clip_context(
            line_threshold = 5,
            token_threshold = 256,
        )).replace("\n\n", "\n").strip()