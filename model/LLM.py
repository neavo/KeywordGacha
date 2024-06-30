import re
import random
import asyncio

from openai import AsyncOpenAI
from helper.TextHelper import TextHelper

from model.Word import Word
from helper.LogHelper import LogHelper


class LLM:

    MAX_RETRY = 2 # 最大重试次数
    MAX_WORKER = 4 # 最大并发工作者数量
    MAX_TOKENS_WORD_EXTRACT = 512 # 单词提取时的最大token数等

    # LLM请求参数配置 - 分词模式
    TOP_P_WORD_EXTRACT = 1
    TEMPERATURE_WORD_EXTRACT = 0
    FREQUENCY_PENALTY_WORD_EXTRACT = 0

    def __init__(self, api_key, base_url, model_name):
        # 初始化OpenAI API密钥、基础URL和模型名称
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        
        # 初始化OpenAI客户端、并发控制信号量以及各类prompt和黑名单
        self.openai_handler = None
        self.semaphore = asyncio.Semaphore(self.MAX_WORKER)
        self.black_list = ""
        self.prompt_extract_words = ""
        self.prompt_translate_surface = ""
        self.prompt_translate_context = ""

        # 初始化OpenAI客户端
        self.init_openai_handler(self.api_key, self.base_url)

    # 使用给定API密钥和基础URL初始化AsyncOpenAI实例
    def init_openai_handler(self, api_key, base_url):
        self.openai_handler = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=120,
            max_retries=0
        )

    # 从指定路径加载黑名单文件内容
    def load_black_list(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.black_list = file.read()
        except FileNotFoundError:
            LogHelper.error("目标文件不存在 ... ")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_extract_words(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_extract_words = file.read()
        except FileNotFoundError:
            LogHelper.error(f"目标文件不存在 ... ")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_translate_surface(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_translate_surface = file.read()
        except FileNotFoundError:
            LogHelper.error(f"目标文件不存在 ... ")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_translate_context(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_translate_context = file.read()
        except FileNotFoundError:
            LogHelper.error(f"目标文件不存在 ... ")

    # 检查是否为有效名词
    def is_valid_noun(self, surface):
        flag = True

        if surface in self.black_list:
            flag = False

        if len(surface) <= 1:
            flag = False

        if not TextHelper.contains_any_japanese(surface):
            flag = False

        # っ和ッ结尾的一般是语气词
        if re.compile(r"^[ぁ-んァ-ン]+[っッ]$").match(surface):
            flag = False

        # if TextHelper.is_all_chinese_or_kanji(token.text) :
        #     continue

        # if len(surface) == 1 and not TextHelper.is_chinese_or_kanji(surface):
        #     flag = False

        return flag

    # 异步发送请求到OpenAI获取模型回复
    async def request(self, text):
        completion = await self.openai_handler.chat.completions.create(
            model=self.model_name,
            temperature=self.TEMPERATURE_WORD_EXTRACT,
            top_p=self.TOP_P_WORD_EXTRACT,
            max_tokens=self.MAX_TOKENS_WORD_EXTRACT,
            frequency_penalty=self.FREQUENCY_PENALTY_WORD_EXTRACT,
            messages=[
                {
                    "role": "system",
                    "content": self.prompt_extract_words,
                },
                {
                    "role": "user", 
                    "content": text
                },
            ],
        )

        llmresponse = completion
        usage = completion.usage
        message = completion.choices[0].message

        return usage, message, llmresponse

    # 异步提取文本中的单词，并过滤无效项
    async def extract_words(self, text, fulltext):
        words = []
        usage, message, llmresponse = await self.request(text)

        if text in ["3", "6", "9"]:
            raise Exception(f"RAISE - {text}")

        # 幻觉，直接抛掉
        if usage.completion_tokens >= self.MAX_TOKENS_WORD_EXTRACT:
            return text, words

        for surface in message.content.split(","):
            surface = surface.strip()

            # 跳过空字符串
            if not surface:
                continue

            # 防止模型瞎编出原文中不存在的词
            if not surface in text:
                continue

            if self.is_valid_noun(surface):
                word = Word()
                word.count = 1
                word.surface = surface
                word.llmresponse = llmresponse
                word.set_context(surface, fulltext)

                words.append(word)

        return text, words

    def _on_extract_words_task_done(self, future, texts, words, texts_failed, texts_successed):
        try:
            text, result = future.result()

            words.extend(result)
            texts_successed.append(text)
            LogHelper.info(f"[LLM 分词] 已完成 {len(texts_successed)} / {len(texts)} ...")       
        except Exception as error:
            LogHelper.warning(f"[LLM 分词] 执行失败，如为超过重试次数，稍后将重试 ...{error}")

        # 此处需要直接修改原有的数组，而不能创建新的数组来赋值
        texts_failed.clear()
        for k, text in enumerate(texts):
            if text not in texts_successed:
                texts_failed.append(text)

    # 批量分词的具体实现
    async def _extract_words_batch(self, texts, fulltext, words, texts_failed, texts_successed):
        if len(texts_failed) == 0:
            texts_this_round = texts
        else:
            texts_this_round = texts_failed

        tasks = []
        async with self.semaphore:
            for k, text in enumerate(texts_this_round):
                task = asyncio.create_task(self.extract_words(text, fulltext))
                task.add_done_callback(lambda future: self._on_extract_words_task_done(future, texts, words, texts_failed, texts_successed))
                tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

        return words, texts_failed, texts_successed

    # 批量分词
    async def extract_words_batch(self, texts, fulltext):
        words = []
        texts_failed = []
        texts_successed = []

        words, texts_failed, texts_successed = await self._extract_words_batch(texts, fulltext, words, texts_failed, texts_successed)

        if len(texts_failed) > 0:
            for i in range(self.MAX_RETRY):
                LogHelper.warning( f"[LLM 分词] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")

                words, texts_failed, texts_successed = await self._extract_words_batch(texts, fulltext, words, texts_failed, texts_successed)
                if len(texts_failed) == 0:
                    break

        return words
