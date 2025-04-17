import re
import threading

import tiktoken
import tiktoken_ext
from tiktoken_ext import openai_public

from base.BaseData import BaseData

class Word(BaseData):

    # 必须显式的引用这两个库，否则打包后会报错
    tiktoken_ext
    openai_public

    # 去重
    RE_DUPLICATE = re.compile(r"[\r\n]+", flags = re.IGNORECASE)

    # 缓存
    CACHE = {}
    CACHE_LOCK = threading.Lock()

    def __init__(self) -> None:
        super().__init__()

        # 默认值
        self.score: float = 0.0
        self.count: int = 0
        self.context: list[str] = []
        self.context_summary: str = ""
        self.context_translation: list[str] = []
        self.surface: str = ""
        self.surface_romaji: str = ""
        self.surface_translation: str = ""
        self.group: str = ""
        self.gender: str = ""
        self.input_lines: list[str] = []

        # 调试信息
        self.llmrequest_surface_analysis: dict = {}
        self.llmrequest_context_translate: dict = {}
        self.llmresponse_surface_analysis: dict = {}
        self.llmresponse_context_translate: dict = {}

    # 获取token数量，优先从缓存中获取
    def get_token_count(self, line: str) -> int:
        count = 0

        # 优先从缓存中取数据
        with Word.CACHE_LOCK:
            if line in Word.CACHE:
                count = Word.CACHE[line]
            else:
                count = len(tiktoken.get_encoding("o200k_base").encode(line))
                Word.CACHE[line] = count

        return count

    # 按阈值截取文本，如果句子长度全部超过阈值，则取最接近阈值的一条
    def clip_lines(self, lines: list[str], line_threshold: int, token_threshold: int) -> tuple[list[str], int]:
        context = []
        context_token_count = 0

        for line in lines:
            # 行数阈值有效，且超过行数阈值，则跳出循环
            if line_threshold > 0 and len(context) > line_threshold:
                break

            line_token_count = self.get_token_count(line)

            # 跳过超出阈值的句子
            if line_token_count > token_threshold:
                continue

            # 更新参考文本与计数
            context.append(line)
            context_token_count = context_token_count + line_token_count

            # 如果计数超过 Token 阈值，则跳出循环
            if context_token_count > token_threshold:
                break

        # 如果句子长度全部超过 Token 阈值，则取最接近阈值的一条
        if len(lines) > 0 and len(context) == 0:
            line = min(lines, key = lambda line: abs(self.get_token_count(line) - token_threshold))

            context.append(line)
            context_token_count = self.get_token_count(line)

        return context, context_token_count

    # 按长度截取参考文本并返回，
    def clip_context(self, line_threshold: int, token_threshold: int) -> list[str]:
        # 先从参考文本中截取
        context, context_token_count = self.clip_lines(self.context, line_threshold, token_threshold)

        # 如果句子长度不足 75%，则尝试全文匹配中补充
        if context_token_count < token_threshold * 0.75:
            context_set = set(self.context)
            context_ex, _ = self.clip_lines(
                sorted(
                    # 筛选出未包含在当前参考文本中且包含关键词的文本以避免重复
                    [line for line in self.input_lines if self.surface in line and line not in context_set],
                    key = lambda line: self.get_token_count(line),
                    reverse = True
                ),
                line_threshold - len(context),
                token_threshold - context_token_count,
            )

            # 追加参考文本
            context.extend(context_ex)

        return context

    # 获取用于参考文本翻译任务的参考文本文本
    def get_context_str_for_translate(self, language: int) -> str:
        from model.NER import NER
        return Word.RE_DUPLICATE.sub(
            "\n",
            "\n".join(
                self.clip_context(
                    line_threshold = 0,
                    token_threshold = 256 if language == NER.Language.EN else 384,
                )
            )
        )

    # 获取用于词义分析任务的参考文本文本
    def get_context_str_for_surface_analysis(self, language: int) -> str:
        from model.NER import NER
        return Word.RE_DUPLICATE.sub(
            "\n",
            "\n".join(
                self.clip_context(
                    line_threshold = 0,
                    token_threshold = 256 if language == NER.Language.EN else 384,
                )
            )
        )