import re
import json
import concurrent.futures

from sudachipy.tokenizer import Tokenizer as SudachipyTokenizer
from sudachipy.dictionary import Dictionary as SudachipyDictionary

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

class NER:

    PART_OF_SPEECH_FILTER = (
        "数詞",
        "サ変可能",
        "副詞可能",
        "形状詞可能",
        "助数詞可能",
        "助動詞語幹",
        "サ変形状詞可能",
    )

    def __init__(self):
        self.blacklist = ""
        self.sudachipy_tokenizer = SudachipyDictionary(dict_type="full").create()
        self.sudachipy_mode = SudachipyTokenizer.SplitMode.B

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

    # 打印词性
    def print_part_of_speech(self, words):
        surface_dict = {}
        attribute_dict = {}
        for k, word in enumerate(words):
            attribute_dict[word.attribute] = word.attribute

            if "人名" in word.attribute:
                surface_dict[word.surface] = word.surface

        for k, v in enumerate(surface_dict.keys()):
                print(k, v)

        for k, v in enumerate(attribute_dict.keys()):
            if "名詞" in v:
                print(k, v)

    # 使用分词器校验
    def check_with_tokenizer(self, word):
        return word.attribute[0] == "名詞" and not any(x in word.attribute for x in self.PART_OF_SPEECH_FILTER)

    # 查找第一类词语 
    def search_for_first_class_words(self, texts, fulltext):
        words = []

        for k, text in enumerate(texts):
            for token in self.sudachipy_tokenizer.tokenize(text, self.sudachipy_mode):
                word = Word()
                word.count = 1
                word.surface = token.surface()
                word.attribute = token.part_of_speech()

                # 判断词性
                if not self.check_with_tokenizer(word):
                    continue

                # 移除纯汉字词
                if not TextHelper.is_all_cjk(word.surface):
                    continue

                # 移除首尾标点符号
                word.surface = TextHelper.strip_punctuation(word.surface)

                # 有效性检查
                if not TextHelper.is_valid_japanese_word(word.surface, self.blacklist):
                    continue

                words.append(word)

            LogHelper.info(f"[查找第一类词语] 已完成 {k + 1} / {len(texts)}")

        return words

    # 查找第二类词语 
    def search_for_second_class_words(self, texts, fulltext):
        words = []

        for k, text in enumerate(texts):
            for token in self.sudachipy_tokenizer.tokenize(text, self.sudachipy_mode):
                word = Word()
                word.count = 1
                word.surface = token.surface()
                word.attribute = token.part_of_speech()

                # 判断词性
                if not self.check_with_tokenizer(word):
                    continue

                # 移除纯汉字词
                if TextHelper.is_all_cjk(word.surface):
                    continue

                # 移除首尾标点符号
                word.surface = TextHelper.strip_punctuation(word.surface)

                # 有效性检查
                if not TextHelper.is_valid_japanese_word(word.surface, self.blacklist):
                    continue

                words.append(word)

            LogHelper.info(f"[查找第二类词语] 已完成 {k + 1} / {len(texts)}")
        return words