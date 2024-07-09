import re
import concurrent.futures

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

class NER:

    def __init__(self):
        self.blacklist = ""

    # 从指定路径加载黑名单文件内容
    def load_blacklist(self, blacklist_path):
        try:
            with open(blacklist_path, "r", encoding="utf-8") as file:
                self.blacklist = file.read()
        except FileNotFoundError:
            LogHelper.error("目标文件不存在 ... ")

    # 查找第一类词语
    def search_for_first_class_words(self, texts, fulltext):
        words = []

        for k, text in enumerate(texts):
            for token in self.tokenizer_sudachipy.tokenize(text, SudachipyTokenizer.Tokenizer.SplitMode.C):
                word = Word()
                word.count = 1
                word.surface = token.surface()
                word.part_of_speech = token.part_of_speech()
                word.set_context(word.surface, fulltext)

                word.surface = TextHelper.strip_punctuation(word.surface)
                word.surface = word.surface.replace("・", "").replace("ー", "ー")

                if not TextHelper.is_valid_japanese_word(word.surface, self.blacklist):
                    continue

                if not TextHelper.is_all_cjk(word.surface):
                    continue

                if not "名詞" in word.part_of_speech:
                    continue

                if "数詞" in word.part_of_speech:
                    continue

                if "サ変可能" in word.part_of_speech:
                    continue

                if "副詞可能" in word.part_of_speech:
                    continue

                if "形状詞可能" in word.part_of_speech:
                    continue

                if "助数詞可能" in word.part_of_speech:
                    continue

                if "助動詞語幹" in word.part_of_speech:
                    continue

                if "サ変形状詞可能" in word.part_of_speech:
                    continue

                words.append(word)
            LogHelper.info(f"[NER 分词] 已完成 {k + 1} / {len(texts)} ...")

        return words

        # 查找第一类词语

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