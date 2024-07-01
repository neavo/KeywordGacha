import re
import random
import asyncio

from openai import AsyncOpenAI

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

class LLM:

    MAX_RETRY = 2 # 最大重试次数
    MAX_WORKER = 4 # 最大并发工作者数量

    TASK_TYPE_EXTRACT_WORD = 1 # 分词模式
    TASK_TYPE_TRANSLATE_SURFACE = 2 # 翻译词表模式
    TASK_TYPE_TRANSLATE_CONTEXT = 3 # 翻译上下文模式

    # LLM请求参数配置 - 分词模式
    TEMPERATURE_WORD_EXTRACT = 0
    TOP_P_WORD_EXTRACT = 1
    MAX_TOKENS_WORD_EXTRACT = 512 
    FREQUENCY_PENALTY_WORD_EXTRACT = 0

    # LLM请求参数配置 - 翻译词表模式
    TEMPERATURE_TRANSLATE_SURFACE = 0
    TOP_P_TRANSLATE_SURFACE = 1
    MAX_TOKENS_TRANSLATE_SURFACE = 512 
    FREQUENCY_PENALTY_TRANSLATE_SURFACE = 0

    # LLM请求参数配置 - 翻译上下文模式
    TEMPERATURE_TRANSLATE_CONTEXT = 0
    TOP_P_TRANSLATE_CONTEXT = 1
    MAX_TOKENS_TRANSLATE_CONTEXT = 1024 
    FREQUENCY_PENALTY_TRANSLATE_CONTEXT = 0

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
            timeout=60,
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
    async def request(self, content, type):
        if type == self.TASK_TYPE_EXTRACT_WORD:
            prmopt = self.prompt_extract_words

            temperature = self.TEMPERATURE_WORD_EXTRACT
            top_p = self.TOP_P_WORD_EXTRACT
            max_tokens = self.MAX_TOKENS_WORD_EXTRACT
            frequency_penalty = self.FREQUENCY_PENALTY_WORD_EXTRACT
        elif type == self.TASK_TYPE_TRANSLATE_SURFACE:
            prmopt = self.prompt_translate_surface

            temperature = self.TEMPERATURE_TRANSLATE_SURFACE
            top_p = self.TOP_P_TRANSLATE_SURFACE
            max_tokens = self.MAX_TOKENS_TRANSLATE_SURFACE
            frequency_penalty = self.FREQUENCY_PENALTY_TRANSLATE_SURFACE
        elif type == self.TASK_TYPE_TRANSLATE_CONTEXT: 
            prmopt = self.prompt_translate_context

            temperature = self.TEMPERATURE_TRANSLATE_CONTEXT
            top_p = self.TOP_P_TRANSLATE_CONTEXT
            max_tokens = self.MAX_TOKENS_TRANSLATE_CONTEXT
            frequency_penalty = self.FREQUENCY_PENALTY_TRANSLATE_CONTEXT

        completion = await self.openai_handler.chat.completions.create(
            model = self.model_name,
            temperature = temperature,
            top_p = top_p,
            max_tokens = max_tokens,
            frequency_penalty = frequency_penalty,
            messages = [
                {
                    "role": "system",
                    "content": prmopt,
                },
                {
                    "role": "user", 
                    "content": content
                },
            ],
        )

        llmresponse = completion
        usage = completion.usage
        message = completion.choices[0].message

        return usage, message, llmresponse

    # 分词任务
    async def extract_words(self, text, fulltext):
        async with self.semaphore:
            words = []
            usage, message, llmresponse = await self.request(text, self.TASK_TYPE_EXTRACT_WORD)

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

    # 分词任务完成时的回调
    def _on_extract_words_task_done(self, future, texts, words, texts_failed, texts_successed):
        try:
            text, result = future.result()
            words.extend(result)
            texts_successed.append(text)
            LogHelper.info(f"[LLM 分词] 已完成 {len(texts_successed)} / {len(texts)} ...")       
        except Exception as error:
            LogHelper.error(f"[LLM 分词] 执行失败，如未超过重试次数，稍后将重试 ... {error}")

        # 此处需要直接修改原有的数组，而不能创建新的数组来赋值
        texts_failed.clear()
        for k, text in enumerate(texts):
            if text not in texts_successed:
                texts_failed.append(text)

    # 批量执行分词任务的具体实现
    async def _extract_words_batch(self, texts, fulltext, words, texts_failed, texts_successed):
        if len(texts_failed) == 0:
            texts_this_round = texts
        else:
            texts_this_round = texts_failed

        tasks = []
        for k, text in enumerate(texts_this_round):
            task = asyncio.create_task(self.extract_words(text, fulltext))
            task.add_done_callback(lambda future: self._on_extract_words_task_done(future, texts, words, texts_failed, texts_successed))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

        return words, texts_failed, texts_successed

    # 批量执分词任务
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

    # 词表翻译任务
    async def translate_surface(self, word):
        async with self.semaphore:
            usage, message, _ = await self.request(word.surface, self.TASK_TYPE_TRANSLATE_SURFACE)

            # 幻觉，直接抛掉
            if usage.completion_tokens >= self.MAX_TOKENS_TRANSLATE_SURFACE:
                return word

            word.surface_translation = message.content.strip().replace("\n", "  ")

            return word

    # 词表翻译任务完成时的回调
    def _on_translate_surface_task_done(self, future, words, words_failed, words_successed):
        try:
            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[后处理 - 词表翻译] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as error:
            LogHelper.error(f"[后处理 - 词表翻译] 执行失败，如未超过重试次数，稍后将重试 ... {error}")

        # 此处需要直接修改原有的数组，而不能创建新的数组来赋值
        words_failed.clear()
        for k, word in enumerate(words):
            if word not in words_successed:
                words_failed.append(word)

    # 批量执行词表翻译任务的具体实现
    async def _translate_surface_batch(self, words, words_failed, words_successed):
        if len(words_failed) == 0:
            words_this_round = words
        else:
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.translate_surface(word))
            task.add_done_callback(lambda future: self._on_translate_surface_task_done(future, words, words_failed, words_successed))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

        return words_failed, words_successed

    # 批量执行词表翻译任务 
    async def translate_surface_batch(self, words):
        words_failed = []
        words_successed = []

        words_failed, words_successed = await self._translate_surface_batch(words, words_failed, words_successed)

        if len(words_failed) > 0:
            for i in range(self.MAX_RETRY):
                LogHelper.warning( f"[后处理 - 词表翻译] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")

                words_failed, words_successed = await self._translate_surface_batch(words, words_failed, words_successed)
                if len(words_failed) == 0:
                    break
        return words

    # 上下文翻译任务
    async def translate_context(self, word):
        async with self.semaphore:
            usage, message, _ = await self.request('\n'.join(word.context), self.TASK_TYPE_TRANSLATE_CONTEXT)

            # 幻觉，直接抛掉
            if usage.completion_tokens >= self.MAX_TOKENS_TRANSLATE_CONTEXT:
                return word

            context_translation = []

            for k, text in enumerate(message.content.strip().split("\n")):
                text = text.strip()
                if len(text) == 0:
                    continue
                context_translation.append(text)

            word.context_translation = context_translation

            return word

    # 上下文翻译任务完成时的回调
    def _on_translate_context_task_done(self, future, words, words_failed, words_successed):
        try:
            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[后处理 - 上下文翻译] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as error:
            LogHelper.error(f"[后处理 - 上下文翻译] 执行失败，如未超过重试次数，稍后将重试 ... {error}")

        # 此处需要直接修改原有的数组，而不能创建新的数组来赋值
        words_failed.clear()
        for k, word in enumerate(words):
            if word not in words_successed:
                words_failed.append(word)

    # 批量执行上下文翻译任务的具体实现
    async def _translate_context_batch(self, words, words_failed, words_successed):
        if len(words_failed) == 0:
            words_this_round = words
        else:
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.translate_context(word))
            task.add_done_callback(lambda future: self._on_translate_context_task_done(future, words, words_failed, words_successed))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

        return words_failed, words_successed

    # 批量执行上下文翻译任务 
    async def translate_context_batch(self, words):
        words_failed = []
        words_successed = []

        words_failed, words_successed = await self._translate_context_batch(words, words_failed, words_successed)

        if len(words_failed) > 0:
            for i in range(self.MAX_RETRY):
                LogHelper.warning( f"[后处理 - 上下文翻译] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")

                words_failed, words_successed = await self._translate_context_batch(words, words_failed, words_successed)
                if len(words_failed) == 0:
                    break
        return words