import os
import re
import json
from collections import Counter
from collections import OrderedDict


class Word:
    def __init__(self):
        self.count = 0
        self.context = []
        self.context_translation = []
        self.surface = ""
        self.surface_translation = ""
        self.llmresponse = ""

    def __str__(self):
        return (
            f"Word(count={self.count},"
            f"context={self.context},"
            f"context_translation={self.context_translation},"
            f"surface={self.surface},"
            f"surface_translation={self.surface_translation},"
            f"llmresponse={self.llmresponse})"
        )

    # 从原文中提取上下文
    def set_context(self, surface, original):
        # 匹配原文
        matches = [line.strip() for line in original if surface in line]
        
        # 使用OrderedDict去除重复并保持顺序
        unique_matches = list(OrderedDict.fromkeys(matches))
        
        # 按长度降序排序
        unique_matches.sort(key=lambda x: (-len(x), x))

        # 取前十个最长的字符串
        top_ten_matches = unique_matches[:10]

        # 赋值给 self.context
        self.context = top_ten_matches
