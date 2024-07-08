import re
import json
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

    TASK_TYPE_EXTRACT_WORD = 10 # 分词
    TASK_TYPE_DETECT_DUPLICATE = 20 # 检测第一类重复词
    TASK_TYPE_SUMMAIRZE_CONTEXT = 30 # 智能总结
    TASK_TYPE_TRANSLATE_SURFACE = 40 # 翻译词语
    TASK_TYPE_TRANSLATE_CONTEXT = 50 # 翻译上下文

    # LLM请求参数配置 - 分词
    TEMPERATURE_WORD_EXTRACT = 0
    TOP_P_WORD_EXTRACT = 1
    MAX_TOKENS_WORD_EXTRACT = 512 
    FREQUENCY_PENALTY_WORD_EXTRACT = 0

    # LLM请求参数配置 - 检测第一类重复词
    TEMPERATURE_SUMMAIRZE_CONTEXT = 0
    TOP_P_SUMMAIRZE_CONTEXT = 1
    MAX_TOKENS_SUMMAIRZE_CONTEXT = 512
    FREQUENCY_PENALTY_SUMMAIRZE_CONTEXT = 0

    # LLM请求参数配置 - 智能总结
    TEMPERATURE_DETECT_DUPLICATE = 0
    TOP_P_DETECT_DUPLICATE = 1
    MAX_TOKENS_DETECT_DUPLICATE = 512
    FREQUENCY_PENALTY_DETECT_DUPLICATE = 0

    # LLM请求参数配置 - 翻译词语
    TEMPERATURE_TRANSLATE_SURFACE = 0
    TOP_P_TRANSLATE_SURFACE = 1
    MAX_TOKENS_TRANSLATE_SURFACE = 512 
    FREQUENCY_PENALTY_TRANSLATE_SURFACE = 0

    # LLM请求参数配置 - 翻译上下文
    TEMPERATURE_TRANSLATE_CONTEXT = 0
    TOP_P_TRANSLATE_CONTEXT = 1
    MAX_TOKENS_TRANSLATE_CONTEXT = 768
    FREQUENCY_PENALTY_TRANSLATE_CONTEXT = 0

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
    def load_prompt_summarize_context(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_summarize_context = file.read()
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

    # 异步发送请求到OpenAI获取模型回复
    async def request(self, prompt, content, type, retry = False):
        if type == self.TASK_TYPE_EXTRACT_WORD:
            temperature = self.TEMPERATURE_WORD_EXTRACT
            top_p = self.TOP_P_WORD_EXTRACT
            max_tokens = self.MAX_TOKENS_WORD_EXTRACT
            frequency_penalty = self.FREQUENCY_PENALTY_WORD_EXTRACT
        elif type == self.TASK_TYPE_SUMMAIRZE_CONTEXT: 
            temperature = self.TEMPERATURE_SUMMAIRZE_CONTEXT
            top_p = self.TOP_P_SUMMAIRZE_CONTEXT
            max_tokens = self.MAX_TOKENS_SUMMAIRZE_CONTEXT
            frequency_penalty = self.FREQUENCY_PENALTY_SUMMAIRZE_CONTEXT
        elif type == self.TASK_TYPE_DETECT_DUPLICATE: 
            temperature = self.TEMPERATURE_DETECT_DUPLICATE
            top_p = self.TOP_P_DETECT_DUPLICATE
            max_tokens = self.MAX_TOKENS_DETECT_DUPLICATE
            frequency_penalty = self.FREQUENCY_PENALTY_DETECT_DUPLICATE
        elif type == self.TASK_TYPE_TRANSLATE_SURFACE:
            temperature = self.TEMPERATURE_TRANSLATE_SURFACE
            top_p = self.TOP_P_TRANSLATE_SURFACE
            max_tokens = self.MAX_TOKENS_TRANSLATE_SURFACE
            frequency_penalty = self.FREQUENCY_PENALTY_TRANSLATE_SURFACE
        elif type == self.TASK_TYPE_TRANSLATE_CONTEXT: 
            temperature = self.TEMPERATURE_TRANSLATE_CONTEXT
            top_p = self.TOP_P_TRANSLATE_CONTEXT
            max_tokens = self.MAX_TOKENS_TRANSLATE_CONTEXT
            frequency_penalty = self.FREQUENCY_PENALTY_TRANSLATE_CONTEXT

        completion = await self.openai_handler.chat.completions.create(
            model = self.model_name,
            temperature = temperature,
            top_p = top_p,
            max_tokens = max_tokens,
            frequency_penalty = 0.2 if retry else frequency_penalty,
            messages = [
                {
                    "role": "system",
                    "content": prompt,
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
    async def extract_words(self, text, fulltext, retry):
        async with self.semaphore:
            words = []
            prompt = self.prompt_extract_words
            task_type = self.TASK_TYPE_EXTRACT_WORD
            usage, message, llmresponse = await self.request(prompt, text, task_type, retry)

            if usage.completion_tokens >= self.MAX_TOKENS_WORD_EXTRACT:
                raise Exception() 

            for surface in message.content.split(","):
                surface = surface.strip()

                # 有效性检查
                if not TextHelper.is_valid_japanese_word(surface, self.black_list):
                    continue

                # 防止模型瞎编出原文中不存在的词
                if not surface in text:
                    continue
                    
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
            LogHelper.warning(f"[LLM 分词] 子任务执行失败，稍后将重试 ... {error}")

    # 批量执行分词任务的具体实现
    async def do_extract_words_batch(self, texts, fulltext, words, texts_failed, texts_successed):
        if len(texts_failed) == 0:
            retry = False
            texts_this_round = texts
        else:
            retry = True
            texts_this_round = texts_failed

        tasks = []
        for k, text in enumerate(texts_this_round):
            task = asyncio.create_task(self.extract_words(text, fulltext, retry))
            task.add_done_callback(lambda future: self.on_extract_words_task_done(future, texts, words, texts_failed, texts_successed))
            tasks.append(task)

        # 等待所有异步任务完成 
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 取所有未成功任务
        texts_failed = [text for text in texts if text not in texts_successed]

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

    # 词语翻译任务
    async def translate_surface(self, word, retry):
        async with self.semaphore:
            prompt = self.prompt_translate_surface.replace("{attribute}", word.attribute)
            task_type = self.TASK_TYPE_TRANSLATE_SURFACE
            usage, message, llmresponse = await self.request(prompt, word.surface, task_type, retry)

            if usage.completion_tokens >= self.MAX_TOKENS_TRANSLATE_SURFACE:
                raise Exception()

            data = json.loads(
                TextHelper.fix_broken_json_string(message.content.strip())
            )

            word.surface_romaji = data["romaji"]
            word.surface_translation = [data["translation_1"], data["translation_2"]]
            word.surface_translation_description = data["description"]

            return word

    # 词语翻译任务完成时的回调
    def on_translate_surface_task_done(self, future, words, words_failed, words_successed):
        try:
            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[词语翻译] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as error:
            LogHelper.warning(f"[词语翻译] 子任务执行失败，稍后将重试 ... {error}")

        # 此处需要直接修改原有的数组，而不能创建新的数组来赋值
        words_failed.clear()
        for k, word in enumerate(words):
            if word not in words_successed:
                words_failed.append(word)

    # 批量执行词语翻译任务的具体实现
    async def do_translate_surface_batch(self, words, words_failed, words_successed):
        if len(words_failed) == 0:
            retry = False
            words_this_round = words
        else:
            retry = True
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.translate_surface(word, retry))
            task.add_done_callback(lambda future: self.on_translate_surface_task_done(future, words, words_failed, words_successed))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

        return words_failed, words_successed

    # 批量执行词语翻译任务 
    async def translate_surface_batch(self, words):
        words_failed = []
        words_successed = []

        words_failed, words_successed = await self.do_translate_surface_batch(words, words_failed, words_successed)

        if len(words_failed) > 0:
            for i in range(self.MAX_RETRY):
                LogHelper.warning( f"[词语翻译] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")

                words_failed, words_successed = await self.do_translate_surface_batch(words, words_failed, words_successed)
                if len(words_failed) == 0:
                    break
        return words

    # 上下文翻译任务
    async def translate_context(self, word, retry):
        async with self.semaphore:
            context_translation = []
            prompt = self.prompt_translate_context
            task_type = self.TASK_TYPE_TRANSLATE_CONTEXT
            usage, message, llmresponse = await self.request(prompt, "\n".join(word.context), task_type, retry)

            if usage.completion_tokens >= self.MAX_TOKENS_TRANSLATE_CONTEXT:
                raise Exception()
            
            for k, line in enumerate(message.content.split("\n")):

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
            LogHelper.info(f"[上下文翻译] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as error:
            LogHelper.warning(f"[上下文翻译] 子任务执行失败，稍后将重试 ... {error}")

        # 此处需要直接修改原有的数组，而不能创建新的数组来赋值
        words_failed.clear()
        for k, word in enumerate(words):
            if word not in words_successed:
                words_failed.append(word)

    # 批量执行上下文翻译任务的具体实现
    async def do_translate_context_batch(self, words, words_failed, words_successed):
        if len(words_failed) == 0:
            retry = False
            words_this_round = words
        else:
            retry = True
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.translate_context(word, retry))
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
                LogHelper.warning( f"[上下文翻译] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                words_failed, words_successed = await self.do_translate_context_batch(words, words_failed, words_successed)

        return words

    # 检测第一类重复词任务
    async def detect_duplicate(self, pair, retry):
        async with self.semaphore:
            prompt = self.prompt_detect_duplicate
            task_type = self.TASK_TYPE_DETECT_DUPLICATE
            usage, message, llmresponse = await self.request(prompt, "\n".join([pair[0].surface, pair[1].surface]), task_type, retry)

            if usage.completion_tokens >= self.MAX_TOKENS_DETECT_DUPLICATE:
                raise Exception() 

            if len(pair) == 3:
                pair[2] = "是" in message.content
            else:
                pair.append("是" in message.content)
            
            return pair

    # 第一类重复词检测任务完成时的回调
    def on_detect_duplicate_task_done(self, future, pairs, pairs_failed, pairs_successed):
        try:
            pair = future.result()
            pairs_successed.append(pair)
            LogHelper.info(f"[第一类重复词检测] 已完成 {len(pairs_successed)} / {len(pairs)} ...")       
        except Exception as error:
            LogHelper.warning(f"[第一类重复词检测] 子任务执行失败，稍后将重试 ... {error}")
 
    # 批量执行第一类重复词检测任务的具体实现
    async def do_detect_duplicate_task(self, pairs, pairs_failed, pairs_successed):
        if len(pairs_failed) == 0:
            retry = False
            pairs_this_round = pairs
        else:
            retry = True
            pairs_this_round = pairs_failed       

        tasks = []
        for k, pair in enumerate(pairs_this_round):
            task = asyncio.create_task(self.detect_duplicate(pair, retry))
            task.add_done_callback(lambda future: self.on_detect_duplicate_task_done(future, pairs, pairs_failed, pairs_successed))
            tasks.append(task)

        # 等待异步任务完成 
        await asyncio.gather(*tasks, return_exceptions=True)

        # 获得失败任务的列表
        pairs_successed_prefixes = {tuple(pair[:2]) for pair in pairs_successed}
        pairs_failed = [pair for pair in pairs if tuple(pair[:2]) not in pairs_successed_prefixes]

        return pairs_failed, pairs_successed

    # 批量执行第一类重复词检测任务
    async def detect_duplicate_batch(self, words):
        pairs_failed = []
        pairs_successed = []
        pairs_need_confirm = []

        # 找出具有第一类重复词的词
        for k_a, word_a in enumerate(words):
            for k_b, word_b in enumerate(words[k_a + 1 :]):
                if word_a.surface in word_b.surface or word_b.surface in word_a.surface:
                    pairs_need_confirm.append([word_a, word_b])

        # 整理字符串对列表，确保每个条目中较短的字符串在前，较长的在后。
        pairs_need_confirm = [[x, y] if len(x.surface) <= len(y.surface) else [y, x] for x, y in pairs_need_confirm]
        
        pairs_failed, pairs_successed = await self.do_detect_duplicate_task(pairs_need_confirm, pairs_failed, pairs_successed)

        for i in range(self.MAX_RETRY):
            if len(pairs_failed) > 0:
                LogHelper.warning( f"[检查第一类重复词] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
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
            LogHelper.info(f"[第一类重复词检测] 正在处理重复词 {surface_a}, {surface_b} ...")    

            for i, word in enumerate(words):
                    words[i].surface = surface_a if word.surface == surface_b else words[i].surface
        
        return words

    # 智能总结任务 
    async def summarize_context(self, word, retry):
        async with self.semaphore:
            prompt = self.prompt_summarize_context.replace("{surface}", word.surface)
            task_type = self.TASK_TYPE_SUMMAIRZE_CONTEXT
            usage, message, _ = await self.request(prompt, "\n".join(word.context), task_type, retry)

            if usage.completion_tokens >= self.MAX_TOKENS_SUMMAIRZE_CONTEXT:
                raise Exception()

            context_summary = json.loads(
                TextHelper.fix_broken_json_string(message.content.strip())
            )

            if "是" in context_summary["person"]:
                word.type = Word.TYPE_PERSON

            if "女" in context_summary["sex"]:
                word.attribute = "女"
            elif "男" in context_summary["sex"]:
                word.attribute = "男"
            else:
                word.attribute = "未知"

            word.context_summary = context_summary

            return word

    # 智能总结任务完成时的回调
    def on_summarize_context_task_done(self, future, words, words_failed, words_successed):
        try:
            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[智能总结] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as error:
            LogHelper.warning(f"[智能总结] 子任务执行失败，稍后将重试 ... {error}")

    # 批量执行智能总结任务的具体实现
    async def do_summarize_context_batch(self, words, words_failed, words_successed):
        if len(words_failed) == 0:
            retry = False
            words_this_round = words
        else:
            retry = True
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.summarize_context(word, retry))
            task.add_done_callback(lambda future: self.on_summarize_context_task_done(future, words, words_failed, words_successed))
            tasks.append(task)

        # 等待异步任务完成 
        await asyncio.gather(*tasks, return_exceptions=True)

        # 获得失败任务的列表
        words_failed = [word_a for word_a in words if not any(word_a.surface == word_b.surface for word_b in words_successed)]

        return words_failed, words_successed

    # 批量执行智能总结任务
    async def summarize_context_batch(self, words):
        words_failed = []
        words_successed = []

        # 第一次请求
        words_failed, words_successed = await self.do_summarize_context_batch(words, words_failed, words_successed)

        # 开始重试流程
        for i in range(self.MAX_RETRY):
            if len(words_failed) > 0:
                LogHelper.warning( f"[智能总结] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                words_failed, words_successed = await self.do_summarize_context_batch(words, words_failed, words_successed)

        return words