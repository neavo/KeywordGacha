import re
import json
import concurrent.futures

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

class NER:

    def __init__(self):
        self.blacklist = ""

    # 从指定路径加载黑名单文件内容
    def load_blacklist(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                data = json.load(file)

                self.blacklist = ""
                for k, v in enumerate(data):
                    self.blacklist = self.blacklist + v + "\n"
        except Exception as error:
            LogHelper.error(f"加载配置文件时发生错误 - {error}")

    # 查找第一类词语 
    def search_for_first_class_words(self, texts, fulltext):
        words = []

        # 匹配所有汉字词语
        for k, v in enumerate(re.findall(rf"[{TextHelper.CJK[0]}-{TextHelper.CJK[1]}]+", "\n".join(fulltext))):
            # 移除首尾标点符号
            v = TextHelper.strip_punctuation(v)

            # 有效性检查
            if not TextHelper.is_valid_japanese_word(v, self.blacklist):
                continue

            word = Word()
            word.count = 1
            word.surface = v

            words.append(word)

        return words

    # 查找第二类词语 
    def search_for_second_class_words(self, texts, fulltext):
        words = []

        # 匹配除了 ・ 以外的所有片假名词语 
        for k, v in enumerate(re.findall(r"[\u30A0-\u30FA\u30FC-\u30FF]+", "\n".join(fulltext))):
            # 移除首尾标点符号
            v = TextHelper.strip_punctuation(v)

            # 有效性检查
            if not TextHelper.is_valid_japanese_word(v, self.blacklist):
                continue

            word = Word()
            word.count = 1
            word.surface = v

            words.append(word)

        return words