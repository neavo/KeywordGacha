import re
import concurrent.futures

import torch
import stanza

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

class NER:

    def __init__(self, config):
        self.black_list = ""
        self.max_workers = config.max_workers
        self.nlp = stanza.Pipeline("ja",
            verbose = False,
            package = None,
            processors = 'tokenize,ner',
            # use_gpu = False,
            model_dir = "santaza\\",
            # download_method = None,
            # langid_clean_text = True,
            tokenize_batch_size = 1024
        )

    # 从指定路径加载黑名单文件内容
    def load_black_list(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.black_list = file.read()
        except FileNotFoundError:
            LogHelper.error("目标文件不存在 ... ")

    # 批量执行分词任务
    def extract_words_batch(self, texts, fulltext):
        words = []

        for k, text in enumerate(texts):
            entitys = self.nlp(text).ents

            for i, entity in enumerate(entitys):
                surface = TextHelper.strip_punctuation(entity.text)

                # 有效性检查
                if not TextHelper.is_valid_japanese_word(surface, self.black_list):
                    continue

                # 词性检查
                if not "PERSON" in entity.type:
                    continue

                word = Word()
                word.count = 1
                word.surface = surface
                word.set_context(surface, fulltext)

                words.append(word)

            LogHelper.info(f"[NER 分词] 已完成 {k + 1} / {len(texts)} ...")

        return words