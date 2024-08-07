import re
import json
from threading import Lock
from collections import Counter
from collections import OrderedDict

import tiktoken
import tiktoken_ext
from tiktoken_ext import openai_public

from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

class Word:

    CONTEXT_CACHE = {}
    CONTEXT_CACHE_LOCK = Lock()
    CONTEXT_TOKEN_THRESHOLD = 768

    MATCH_LENGTHS_CACHE = {}
    MATCH_LENGTHS_CACHE_LOCK = Lock()

    def __init__(self):
        self.score = 0
        self.count = 0
        self.context = []
        self.context_summary = {}
        self.context_translation = []
        self.surface = ""
        self.surface_romaji = ""
        self.surface_translation = ["", ""]
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

    # 从原文中提取上下文
    def search_context(self, original):
        if self.surface in Word.CONTEXT_CACHE:
            with Word.CONTEXT_CACHE_LOCK:
                return Word.CONTEXT_CACHE.get(self.surface)
        else:
            # 创建一个字典来存储每个匹配项及其编码后的长度
            match_lengths = {}

            # 匹配原文并去重
            for line in original:
                if self.surface in line:
                    # 检查缓存中是否有该行的长度
                    with Word.MATCH_LENGTHS_CACHE_LOCK:
                        if line not in Word.MATCH_LENGTHS_CACHE:
                            Word.MATCH_LENGTHS_CACHE[line] = len(self.tiktoken_encoding.encode(line))
                        match_lengths[line] = Word.MATCH_LENGTHS_CACHE[line]

            # 按长度降序排序
            sorted_matches = sorted(match_lengths.items(), key = lambda item: (-item[1], item[0]))

            # 在阈值范围内取 Token 最长的条数
            context = []
            context_length = 0
            for line, length in sorted_matches:
                if context_length + length > self.CONTEXT_TOKEN_THRESHOLD:
                    break

                context.append(line)
                context_length += length

            # 将结果保存到缓存中
            with Word.CONTEXT_CACHE_LOCK:
                Word.CONTEXT_CACHE[self.surface] = context

            return context

    # 按长度截取上下文并返回
    def clip_context(self, threshold):
        context = []
        context_length = 0
        for k, line in enumerate(self.context):
            line_lenght = len(self.tiktoken_encoding.encode(line))

            if context_length + line_lenght > threshold:
                break

            context.append(line)
            context_length = context_length + line_lenght

        return context
