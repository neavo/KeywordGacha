import os
import re
import json
from collections import Counter

class Word:
    def __init__(self):
        self.count = 0
        self.context = []
        self.context_translation = []
        self.surface = ""
        self.surface_translation = ""
        self.llmresponse = ""

    # 从原文中提取上下文
    def set_context(self, surface, original):
        
        # 匹配原文
        matches = []
        for line in original:
            if surface in line:
                matches.append(line.strip())    

        # 按长度降序排序
        matches.sort(key=lambda x: (len(x), x), reverse=True)
        
        # 取前十个最长的字符串
        top_ten_matches = matches[:10] if len(matches) >= 10 else matches
        
        # 赋值给 self.context
        self.context = top_ten_matches