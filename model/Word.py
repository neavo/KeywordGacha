import re
import json

import tiktoken
import tiktoken_ext
from tiktoken_ext import openai_public

from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

class Word:

    def __init__(self):
        self.score = 0
        self.count = 0
        self.context = []
        self.context_summary = ""
        self.context_translation = []
        self.surface = ""
        self.surface_romaji = ""
        self.surface_translation = ""
        self.surface_translation_description = ""
        self.ner_type = ""
        self.attribute = ""
        self.llmresponse_summarize_context = ""
        self.llmresponse_translate_context = ""
        self.llmresponse_translate_surface = ""

        self.tiktoken_encoding = tiktoken.get_encoding("cl100k_base")

    def __str__(self):
        return (
            f"Word(score={self.score},"
            f"count={self.count},"
            f"context={self.context},"
            f"context_summary={self.context_summary},"
            f"context_translation={self.context_translation},"
            f"surface={self.surface},"
            f"surface_romaji={self.surface_romaji},"
            f"surface_translation={self.surface_translation},"
            f"surface_translation_description={self.surface_translation_description},"
            f"ner_type={self.ner_type},"
            f"attribute={self.attribute},"
            f"llmresponse_summarize_context={self.llmresponse_summarize_context},"
            f"llmresponse_translate_context={self.llmresponse_translate_context},"
            f"llmresponse_translate_surface={self.llmresponse_translate_surface})"
        )

    # 按长度截取上下文并返回，至少取一条与阈值最接近的
    def clip_context(self, threshold):
        # 理论上不应该有上下文为空的情况
        # TODO : FIX
        if not self.context:
            LogHelper.debug(f"{self.surface} - {self.ner_type} - {self.count} - {self.context} ...")
            return []

        context = []
        context_length = 0

        for line in self.context:
            line_length = len(self.tiktoken_encoding.encode(line))

            if line_length > threshold:
                continue  # 跳过超出阈值的句子

            if context_length + line_length > threshold:
                break

            context.append(line)
            context_length += line_length

        # 如果没有找到合适的句子，取最接近阈值的一条
        if not context:
            closest_line = min(self.context, key = lambda line: abs(len(self.tiktoken_encoding.encode(line)) - threshold))
            context.append(closest_line)

        return context
