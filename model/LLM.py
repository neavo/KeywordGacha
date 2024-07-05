import re
import random
import asyncio

import tiktoken
import tiktoken_ext
from tiktoken_ext import openai_public
from openai import AsyncOpenAI

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

class LLM:

    MAX_RETRY = 2 # 最大重试次数
    DEGRADATION_FLAG = "[☀️DEGRADATION☀️]" # 用于标识退化

    TASK_TYPE_EXTRACT_WORD = 10 # 分词模式
    TASK_TYPE_EXTRACT_WORD_DEGRADATION = 11 # 分词模式退化重试
    TASK_TYPE_TRANSLATE_SURFACE = 20 # 翻译词表模式
    TASK_TYPE_TRANSLATE_CONTEXT = 30 # 翻译上下文模式
    TASK_TYPE_DETECT_DUPLICATE = 40 # 检测重复词根模式

    # LLM请求参数配置 - 分词模式
    TEMPERATURE_WORD_EXTRACT = 0
    TOP_P_WORD_EXTRACT = 1
    MAX_TOKENS_WORD_EXTRACT = 512 
    FREQUENCY_PENALTY_WORD_EXTRACT = 0

    # LLM请求参数配置 - 分词模式退化重试
    TEMPERATURE_WORD_EXTRACT_DEGRADATION = 0
    TOP_P_WORD_EXTRACT_DEGRADATION = 1
    MAX_TOKENS_WORD_EXTRACT_DEGRADATION = 512 
    FREQUENCY_PENALTY_WORD_EXTRACT_DEGRADATION = 0.2

    # LLM请求参数配置 - 翻译词表模式
    TEMPERATURE_TRANSLATE_SURFACE = 0
    TOP_P_TRANSLATE_SURFACE = 1
    MAX_TOKENS_TRANSLATE_SURFACE = 512 
    FREQUENCY_PENALTY_TRANSLATE_SURFACE = 0

    # LLM请求参数配置 - 翻译上下文模式
    TEMPERATURE_TRANSLATE_CONTEXT = 0
    TOP_P_TRANSLATE_CONTEXT = 1
    MAX_TOKENS_TRANSLATE_CONTEXT_REQUEST = 512
    MAX_TOKENS_TRANSLATE_CONTEXT_RESPONSE = 1024
    FREQUENCY_PENALTY_TRANSLATE_CONTEXT = 0

    # LLM请求参数配置 - 检测重复词根模式
    TEMPERATURE_DETECT_DUPLICATE = 0
    TOP_P_DETECT_DUPLICATE = 1
    MAX_TOKENS_DETECT_DUPLICATE = 512
    FREQUENCY_PENALTY_DETECT_DUPLICATE = 0

    def __init__(self, config):
        # 初始化OpenAI API密钥、基础URL和模型名称
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.model_name = config.model_name
        
        # 初始化各类prompt和黑名单
        self.black_list = ""
        self.prompt_extract_words = ""
        self.prompt_translate_surface = ""
        self.prompt_translate_context = ""

        # OpenAI客户端相关参数
        self.openai_handler = None
        self.semaphore = asyncio.Semaphore(config.max_workers)

        # 初始化OpenAI客户端
        self.tiktoken_encoding = tiktoken.get_encoding("cl100k_base")
        self.openai_handler = AsyncOpenAI(
            api_key = self.api_key,
            base_url = self.base_url,
            timeout = config.request_timeout,
            max_retries = 0
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
    def load_prompt_detect_duplicate(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_detect_duplicate = file.read()
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
        elif type == self.TASK_TYPE_EXTRACT_WORD_DEGRADATION:
            prmopt = self.prompt_extract_words
            temperature = self.TEMPERATURE_WORD_EXTRACT_DEGRADATION
            top_p = self.TOP_P_WORD_EXTRACT_DEGRADATION
            max_tokens = self.MAX_TOKENS_WORD_EXTRACT_DEGRADATION
            frequency_penalty = self.FREQUENCY_PENALTY_WORD_EXTRACT_DEGRADATION
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
            max_tokens = self.MAX_TOKENS_TRANSLATE_CONTEXT_RESPONSE
            frequency_penalty = self.FREQUENCY_PENALTY_TRANSLATE_CONTEXT
        elif type == self.TASK_TYPE_DETECT_DUPLICATE: 
            prmopt = self.prompt_detect_duplicate

            temperature = self.TEMPERATURE_DETECT_DUPLICATE
            top_p = self.TOP_P_DETECT_DUPLICATE
            max_tokens = self.MAX_TOKENS_DETECT_DUPLICATE
            frequency_penalty = self.FREQUENCY_PENALTY_DETECT_DUPLICATE

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

            if not text.startswith(self.DEGRADATION_FLAG):
                usage, message, llmresponse = await self.request(text, self.TASK_TYPE_EXTRACT_WORD)
            else:
                text = text.replace(self.DEGRADATION_FLAG, "")
                usage, message, llmresponse = await self.request(text, self.TASK_TYPE_EXTRACT_WORD_DEGRADATION)

            if usage.completion_tokens >= self.MAX_TOKENS_WORD_EXTRACT:
                raise Exception(self.DEGRADATION_FLAG + text) 

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
    def on_extract_words_task_done(self, future, texts, words, texts_failed, texts_successed):
        try:
            text, result = future.result()
            words.extend(result)
            texts_successed.append(text)
            LogHelper.info(f"[LLM 分词] 已完成 {len(texts_successed)} / {len(texts)} ...")       
        except Exception as error:
            error_message = str(error)

            if error_message.startswith(self.DEGRADATION_FLAG):
                LogHelper.warning(f"[LLM 分词] 收到了不正确的回复，稍后将重试 ...")
            else:
                LogHelper.error(f"[LLM 分词] 执行失败，稍后将重试 ... {error_message} ...")

    # 批量执行分词任务的具体实现
    async def do_extract_words_batch(self, texts, fulltext, words, texts_failed, texts_successed):
        if len(texts_failed) == 0:
            texts_this_round = texts
        else:
            texts_this_round = texts_failed

        tasks = []
        for k, text in enumerate(texts_this_round):
            task = asyncio.create_task(self.extract_words(text, fulltext))
            task.add_done_callback(lambda future: self.on_extract_words_task_done(future, texts, words, texts_failed, texts_successed))
            tasks.append(task)

        # 等待所有异步任务完成 
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 取所有未成功任务
        texts_failed = [text for text in texts if text not in texts_successed]

        # 遍历所有任务的结果，找到标记为退化的任务，并修改列表中的对应的条目
        for k, result in enumerate(results):
            if isinstance(result, Exception) and str(result).startswith(self.DEGRADATION_FLAG):
                pure_text = str(result).replace(self.DEGRADATION_FLAG, "")
                error_text = str(result)

                for k, text in enumerate(texts_failed):
                    if text == pure_text:
                        texts_failed[k] = error_text 
                        break

        return words, texts_failed, texts_successed

    # 批量执分词任务
    async def extract_words_batch(self, texts, fulltext):
        words = []
        texts_failed = []
        texts_successed = []

        words, texts_failed, texts_successed = await self.do_extract_words_batch(texts, fulltext, words, texts_failed, texts_successed)

        if len(texts_failed) > 0:
            for i in range(self.MAX_RETRY):
                LogHelper.warning( f"[LLM 分词] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")

                words, texts_failed, texts_successed = await self.do_extract_words_batch(texts, fulltext, words, texts_failed, texts_successed)
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
    def on_translate_surface_task_done(self, future, words, words_failed, words_successed):
        try:
            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[后处理 - 词表翻译] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as error:
            LogHelper.error(f"[后处理 - 词表翻译] 执行失败，稍后将重试 ... {error}")

        # 此处需要直接修改原有的数组，而不能创建新的数组来赋值
        words_failed.clear()
        for k, word in enumerate(words):
            if word not in words_successed:
                words_failed.append(word)

    # 实际执行词表翻译任务
    async def do_translate_surface_batch(self, words, words_failed, words_successed):
        if len(words_failed) == 0:
            words_this_round = words
        else:
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.translate_surface(word))
            task.add_done_callback(lambda future: self.on_translate_surface_task_done(future, words, words_failed, words_successed))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

        return words_failed, words_successed

    # 批量执行词表翻译任务 
    async def translate_surface_batch(self, words):
        words_failed = []
        words_successed = []

        words_failed, words_successed = await self.do_translate_surface_batch(words, words_failed, words_successed)

        if len(words_failed) > 0:
            for i in range(self.MAX_RETRY):
                LogHelper.warning( f"[后处理 - 词表翻译] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")

                words_failed, words_successed = await self.do_translate_surface_batch(words, words_failed, words_successed)
                if len(words_failed) == 0:
                    break
        return words

    # 执行上下文任务的合并   
    def do_context_merge(self, context):
        current_size = 0
        current_segment = []
        context_split_by_token = []

        for line in context:
            line_token = len(self.tiktoken_encoding.encode(line))

            # 如果当前段的大小加上当前行的大小超过阈值，则需要将当前段添加到结果列表中，并重置当前段
            if current_size + line_token > self.MAX_TOKENS_TRANSLATE_CONTEXT_REQUEST:
                context_split_by_token.append("\n".join(current_segment))
                current_segment = []
                current_size = 0

            # 添加当前字符串到当前段
            current_segment.append(line)
            current_size += line_token

        # 添加最后一段
        if current_segment:
            context_split_by_token.append("\n".join(current_segment))

        return context_split_by_token

    # 上下文翻译任务
    async def translate_context(self, word):
        async with self.semaphore:
            context_translation = []
            context_split_by_token = self.do_context_merge(word.context)
            for k, line in enumerate(context_split_by_token):
                usage, message, _ = await self.request(line, self.TASK_TYPE_TRANSLATE_CONTEXT)

                # 幻觉，直接抛掉
                if usage.completion_tokens >= self.MAX_TOKENS_TRANSLATE_CONTEXT_RESPONSE:
                    continue
                lines = message.content.split("\n")
                for k, line in enumerate(lines):
                    # 比之前稍微好了一点，但是还是很丑陋
                    line = line.replace("\n", "")
                    line = re.sub(r"(第.行)?翻译文本：?", "", line)
                    line = re.sub(r"第.行：?", "", line)
                    line = line.strip()                

                    if len(line) > 0:
                        context_translation.append(line)

            word.context_translation = context_translation

            return word

    # 上下文翻译任务完成时的回调
    def on_translate_context_task_done(self, future, words, words_failed, words_successed):
        try:
            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[后处理 - 上下文翻译] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as error:
            LogHelper.error(f"[后处理 - 上下文翻译] 执行失败，稍后将重试 ... {error}")

        # 此处需要直接修改原有的数组，而不能创建新的数组来赋值
        words_failed.clear()
        for k, word in enumerate(words):
            if word not in words_successed:
                words_failed.append(word)

    # 实际执行上下文翻译任务
    async def do_translate_context_batch(self, words, words_failed, words_successed):
        if len(words_failed) == 0:
            words_this_round = words
        else:
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.translate_context(word))
            task.add_done_callback(lambda future: self.on_translate_context_task_done(future, words, words_failed, words_successed))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

        return words_failed, words_successed

    # 批量执行上下文翻译任务 
    async def translate_context_batch(self, words):
        words_failed = []
        words_successed = []

        words_failed, words_successed = await self.do_translate_context_batch(words, words_failed, words_successed)

        for i in range(self.MAX_RETRY):
            if len(words_failed) > 0:
                LogHelper.warning( f"[后处理 - 上下文翻译] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                words_failed, words_successed = await self.do_translate_context_batch(words, words_failed, words_successed)

        return words

    # 检测重复词根任务
    async def detect_duplicate(self, pair):
        async with self.semaphore:
            content = "\n".join([pair[0].surface, pair[1].surface])
            usage, message, llmresponse = await self.request((content), self.TASK_TYPE_DETECT_DUPLICATE)

            if usage.completion_tokens >= self.MAX_TOKENS_DETECT_DUPLICATE:
                raise Exception() 

            if len(pair) >= 3:
                pair[2] = message.content == "是"
            else:
                pair.append(message.content == "是")
            
            return pair

    # 重复词根检测任务完成时的回调
    def on_detect_duplicate_task_done(self, future, pairs, pairs_failed, pairs_successed):
        try:
            pair = future.result()
            pairs_successed.append(pair)
            LogHelper.info(f"[重复词根检测] 已完成 {len(pairs_successed)} / {len(pairs)} ...")       
        except Exception as error:
            LogHelper.error(f"[重复词根检测] 执行失败，稍后将重试 ... {error}")
 
     # 实际执行重复词根检测任务

    # 实际执行重复词根检测任务 
    async def do_detect_duplicate_task(self, pairs, pairs_failed, pairs_successed):
        if len(pairs_failed) == 0:
            pairs_this_round = pairs
        else:
            pairs_this_round = pairs_failed       

        tasks = []
        for k, pair in enumerate(pairs_this_round):
            task = asyncio.create_task(self.detect_duplicate(pair))
            task.add_done_callback(lambda future: self.on_detect_duplicate_task_done(future, pairs, pairs_failed, pairs_successed))
            tasks.append(task)

        # 等待异步任务完成 
        await asyncio.gather(*tasks, return_exceptions=True)

        # 取所有未成功任务
        pairs_successed_prefixes = {tuple(pair[:2]) for pair in pairs_successed}
        pairs_failed = [pair for pair in pairs if tuple(pair[:2]) not in pairs_successed_prefixes]

        return pairs_failed, pairs_successed

    # 批量执行重复词根检测任务
    async def detect_duplicate_batch(self, words):
        pairs_failed = []
        pairs_successed = []
        pairs_need_confirm = []

        # 找出具有重复词根的词
        for k_a, word_a in enumerate(words):
            for k_b, word_b in enumerate(words[k_a + 1 :]):
                if word_a.surface in word_b.surface or word_b.surface in word_a.surface:
                    pairs_need_confirm.append([word_a, word_b])

        # 整理字符串对列表，确保每个条目中较短的字符串在前，较长的在后。
        pairs_need_confirm = [[x, y] if len(x.surface) <= len(y.surface) else [y, x] for x, y in pairs_need_confirm]
        
        pairs_failed, pairs_successed = await self.do_detect_duplicate_task(pairs_need_confirm, pairs_failed, pairs_successed)

        for i in range(self.MAX_RETRY):
            if len(pairs_failed) > 0:
                LogHelper.warning( f"[检查重复词根] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                pairs_failed, pairs_successed = await self.do_detect_duplicate_task(pairs_need_confirm, pairs_failed, pairs_successed)

        # 筛选判断为重复词的条目
        pairs_successed = [pair for pair in pairs_successed if pair[2] == True]

        # 排序，长的排在前面
        pairs_successed = sorted(
            pairs_successed, key=lambda pair: (pair[0].surface, -len(pair[1].surface))
        )

        for k, (word_a, word_b, flag) in enumerate(pairs_successed):
            surface_a = word_a.surface
            surface_b = word_b.surface
            LogHelper.info(f"[重复词根检测] 正在处理重复词 {surface_a}, {surface_b} ...")    

            for i, word in enumerate(words):
                    words[i].surface = surface_a if word.surface == surface_b else words[i].surface
        
        return words