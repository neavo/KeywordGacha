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

    TASK_TYPE_FIRST_CLASS_ATTRIBUTE = 20 # 判断第一类词语词性判断
    TASK_TYPE_SECOND_CLASS_ATTRIBUTE = 30 # 判断第二类词语词性判断
    TASK_TYPE_SUMMAIRZE_CONTEXT = 50 # 词义分析
    TASK_TYPE_TRANSLATE_SURFACE = 60 # 翻译词语
    TASK_TYPE_TRANSLATE_CONTEXT = 70 # 翻译上下文

    # 请求参数配置 - 判断第一类词语词性判断
    TEMPERATURE_FIRST_CLASS_ATTRIBUTE = 0
    TOP_P_FIRST_CLASS_ATTRIBUTE = 0.99
    MAX_TOKENS_FIRST_CLASS_ATTRIBUTE = 512
    FREQUENCY_PENALTY_FIRST_CLASS_ATTRIBUTE = 0

    # 请求参数配置 - 判断第二类词语词性判断
    TEMPERATURE_SECOND_CLASS_ATTRIBUTE = 0
    TOP_P_SECOND_CLASS_ATTRIBUTE = 0.99
    MAX_TOKENS_SECOND_CLASS_ATTRIBUTE = 512
    FREQUENCY_PENALTY_SECOND_CLASS_ATTRIBUTE = 0

    # 请求参数配置 - 词义分析
    TEMPERATURE_SUMMAIRZE_CONTEXT = 0
    TOP_P_SUMMAIRZE_CONTEXT = 0.99
    MAX_TOKENS_SUMMAIRZE_CONTEXT = 512
    FREQUENCY_PENALTY_SUMMAIRZE_CONTEXT = 0

    # 请求参数配置 - 翻译词语
    TEMPERATURE_TRANSLATE_SURFACE = 0
    TOP_P_TRANSLATE_SURFACE = 0.99
    MAX_TOKENS_TRANSLATE_SURFACE = 512 
    FREQUENCY_PENALTY_TRANSLATE_SURFACE = 0

    # 请求参数配置 - 翻译上下文
    TEMPERATURE_TRANSLATE_CONTEXT = 0
    TOP_P_TRANSLATE_CONTEXT = 0.99
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
        self.prompt_first_class_attribute = ""
        self.prompt_second_class_attribute = ""
        self.prompt_detect_duplicate = ""
        self.prompt_summarize_context = ""
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
    def load_blacklist(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                data = json.load(file)

                self.blacklist = ""
                for k, v in enumerate(data):
                    self.blacklist = self.blacklist + v + "\n"
        except Exception as error:
            LogHelper.error(f"加载配置文件时发生错误 - {error}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_first_class_attribute(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_first_class_attribute = file.read()
        except FileNotFoundError:
            LogHelper.error(f"目标文件不存在 ... ")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_second_class_attribute(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_second_class_attribute = file.read()
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
    async def request(self, prompt, content, task_type, retry = False):
        if task_type == self.TASK_TYPE_SUMMAIRZE_CONTEXT: 
            temperature = self.TEMPERATURE_SUMMAIRZE_CONTEXT
            top_p = self.TOP_P_SUMMAIRZE_CONTEXT
            max_tokens = self.MAX_TOKENS_SUMMAIRZE_CONTEXT
            frequency_penalty = self.FREQUENCY_PENALTY_SUMMAIRZE_CONTEXT
        elif task_type == self.TASK_TYPE_FIRST_CLASS_ATTRIBUTE: 
            temperature = self.TEMPERATURE_FIRST_CLASS_ATTRIBUTE
            top_p = self.TOP_P_FIRST_CLASS_ATTRIBUTE
            max_tokens = self.MAX_TOKENS_FIRST_CLASS_ATTRIBUTE
            frequency_penalty = self.FREQUENCY_PENALTY_FIRST_CLASS_ATTRIBUTE
        elif task_type == self.TASK_TYPE_SECOND_CLASS_ATTRIBUTE: 
            temperature = self.TEMPERATURE_SECOND_CLASS_ATTRIBUTE
            top_p = self.TOP_P_SECOND_CLASS_ATTRIBUTE
            max_tokens = self.MAX_TOKENS_SECOND_CLASS_ATTRIBUTE
            frequency_penalty = self.FREQUENCY_PENALTY_SECOND_CLASS_ATTRIBUTE
        elif task_type == self.TASK_TYPE_TRANSLATE_SURFACE:
            temperature = self.TEMPERATURE_TRANSLATE_SURFACE
            top_p = self.TOP_P_TRANSLATE_SURFACE
            max_tokens = self.MAX_TOKENS_TRANSLATE_SURFACE
            frequency_penalty = self.FREQUENCY_PENALTY_TRANSLATE_SURFACE
        elif task_type == self.TASK_TYPE_TRANSLATE_CONTEXT: 
            temperature = self.TEMPERATURE_TRANSLATE_CONTEXT
            top_p = self.TOP_P_TRANSLATE_CONTEXT
            max_tokens = self.MAX_TOKENS_TRANSLATE_CONTEXT
            frequency_penalty = self.FREQUENCY_PENALTY_TRANSLATE_CONTEXT

        completion = await self.openai_handler.chat.completions.create(
            model = self.model_name,
            temperature = temperature,
            top_p = top_p,
            max_tokens = max_tokens,
            frequency_penalty = frequency_penalty + 0.2 if retry else frequency_penalty,
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

    # 词性判断任务
    async def analyze_attribute(self, word, task_type, retry):
        async with self.semaphore:
            if task_type == self.TASK_TYPE_FIRST_CLASS_ATTRIBUTE:
                prompt = self.prompt_first_class_attribute
                max_tokens = self.MAX_TOKENS_FIRST_CLASS_ATTRIBUTE
            elif task_type == self.TASK_TYPE_SECOND_CLASS_ATTRIBUTE:
                prompt = self.prompt_second_class_attribute
                max_tokens = self.MAX_TOKENS_SECOND_CLASS_ATTRIBUTE

            usage, message, llmresponse = await self.request(prompt, word.surface, task_type, retry)

            if usage.completion_tokens >= max_tokens:
                raise Exception()

            surface =  message.content.strip()

            if task_type == self.TASK_TYPE_FIRST_CLASS_ATTRIBUTE:
                if any(v in surface for v in ["无", "否", "無", "no", "none"]):
                    return word

                word.type = Word.TYPE_NOUN
            elif task_type == self.TASK_TYPE_SECOND_CLASS_ATTRIBUTE:
                if any(v in surface for v in ["无", "否", "無", "no", "none"]):
                    return word

                if not TextHelper.is_valid_japanese_word(surface, self.black_list):
                    return word

                word.type = Word.TYPE_NOUN
                word.surface = surface

            return word

    # 词性判断任务完成时的回调
    def on_analyze_attribute_task_done(self, future, words, words_failed, words_successed, task_type):
        try:
            task_name = "第一类词语词性判断" if task_type == self.TASK_TYPE_FIRST_CLASS_ATTRIBUTE else "第二类词语词性判断"

            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[{task_name}] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as error:
            LogHelper.warning(f"[{task_name}] 子任务执行失败，稍后将重试 ... {error}")

    # 批量执行词性判断任务的具体实现
    async def do_analyze_attribute_batch(self, words, words_failed, words_successed, task_type):
        if len(words_failed) == 0:
            retry = False
            words_this_round = words
        else:
            retry = True
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.analyze_attribute(word, task_type, retry))
            task.add_done_callback(lambda future: self.on_analyze_attribute_task_done(future, words, words_failed, words_successed, task_type))
            tasks.append(task)

        # 等待异步任务完成 
        await asyncio.gather(*tasks, return_exceptions=True)

        # 获得失败任务的列表
        words_failed = [word_a for word_a in words if not any(word_a.surface == word_b.surface for word_b in words_successed)]

        return words_failed, words_successed

    # 批量执行词性判断任务
    async def analyze_attribute_batch(self, words, task_type):
        words_failed = []
        words_successed = []
        task_name = "第一类词语词性判断" if task_type == self.TASK_TYPE_FIRST_CLASS_ATTRIBUTE else "第二类词语词性判断"

        # 第一次请求
        words_failed, words_successed = await self.do_analyze_attribute_batch(words, words_failed, words_successed, task_type)

        # 开始重试流程
        for i in range(self.MAX_RETRY):
            if len(words_failed) > 0:
                LogHelper.warning( f"[{task_name}] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                words_failed, words_successed = await self.do_analyze_attribute_batch(words, words_failed, words_successed, task_type)

        return words

    # 词语翻译任务
    async def translate_surface(self, word, retry):
        async with self.semaphore:
            prompt = self.prompt_translate_surface.replace("{attribute}", word.attribute)
            task_type = self.TASK_TYPE_TRANSLATE_SURFACE
            usage, message, llmresponse = await self.request(prompt, word.surface, task_type, retry)

            if usage.completion_tokens >= self.MAX_TOKENS_TRANSLATE_SURFACE:
                raise Exception()

            try:
                data = json.loads(
                    TextHelper.fix_broken_json_string(message.content.strip())
                )
            except Exception as error:
                LogHelper.debug(message.content.strip())
                raise error

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

    # 词义分析任务 
    async def summarize_context(self, word, retry):
        async with self.semaphore:
            prompt = self.prompt_summarize_context.replace("{surface}", word.surface)
            task_type = self.TASK_TYPE_SUMMAIRZE_CONTEXT
            usage, message, llmresponse = await self.request(prompt, "\n".join(word.context), task_type, retry)

            if usage.completion_tokens >= self.MAX_TOKENS_SUMMAIRZE_CONTEXT:
                raise Exception()

            try:
                context_summary = json.loads(
                    TextHelper.fix_broken_json_string(message.content.strip())
                )
            except Exception as error:
                LogHelper.debug(message.content.strip())
                raise error

            if "是" in context_summary["person"] or "は" in context_summary["person"]:
                word.type = Word.TYPE_PERSON
            else:
                LogHelper.debug(f"context_summary.person = false - {word.surface}")
           
            if "女" in context_summary["sex"]:
                word.attribute = "女"
            elif "男" in context_summary["sex"]:
                word.attribute = "男"
            else:
                word.attribute = "未知"

            word.context_summary = context_summary

            return word

    # 词义分析任务完成时的回调
    def on_summarize_context_task_done(self, future, words, words_failed, words_successed):
        try:
            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[词义分析] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as error:
            LogHelper.warning(f"[词义分析] 子任务执行失败，稍后将重试 ... {error}")

    # 批量执行词义分析任务的具体实现
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

    # 批量执行词义分析任务
    async def summarize_context_batch(self, words):
        words_failed = []
        words_successed = []

        # 第一次请求
        words_failed, words_successed = await self.do_summarize_context_batch(words, words_failed, words_successed)

        # 开始重试流程
        for i in range(self.MAX_RETRY):
            if len(words_failed) > 0:
                LogHelper.warning( f"[词义分析] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                words_failed, words_successed = await self.do_summarize_context_batch(words, words_failed, words_successed)

        return words