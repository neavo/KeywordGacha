import os
import re
import json
from collections import Counter
from collections import OrderedDict

import tiktoken
import tiktoken_ext
from tiktoken_ext import openai_public

class Word:

    CONTEXT_TOKEN_THRESHOLD = 768

    def __init__(self):
        self.count = 0
        self.context = []
        self.context_summary = ""
        self.context_translation = []
        self.surface = ""
        self.surface_translation = ""
        self.attribute = ""
        self.llmresponse = ""

        self.tiktoken_encoding = tiktoken.get_encoding("cl100k_base")

    def __str__(self):
        return (
            f"Word(count={self.count},"
            f"context={self.context},"
            f"context_summary={self.context_summary},"
            f"context_translation={self.context_translation},"
            f"surface={self.surface},"
            f"surface_translation={self.surface_translation},"
            f"attribute={self.attribute},"
            f"llmresponse={self.llmresponse})"
        )

    # 从原文中提取上下文
    def set_context(self, surface, original):
        # 匹配原文
        matches = [line.strip() for line in original if surface in line]
        
        # 使用OrderedDict去除重复并保持顺序
        unique_matches = list(OrderedDict.fromkeys(matches))
        
        # 按长度降序排序
        unique_matches.sort(key=lambda x: (-len(self.tiktoken_encoding.encode(x)), x))

        # 取按 Token 计算最长的十条，但是 Token 长度之和不超过阈值
        context = []
        context_length = 0
        for k, line in enumerate(unique_matches):
            line_lenght = len(self.tiktoken_encoding.encode(line))

            if len(context) >= 10:
                break

            if context_length + line_lenght > self.CONTEXT_TOKEN_THRESHOLD:
                break

            context.append(line)
            context_length = context_length + line_lenght

        # 赋值给 self.context
        self.context = context
