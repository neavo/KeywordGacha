import re
import json
import random
import asyncio

from openai import AsyncOpenAI
from aiolimiter import AsyncLimiter

from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

class LLM:

    MAX_RETRY = 2 # 最大重试次数

    TASK_TYPE_ANALYZE_ATTRIBUTE = 10 # 判断词性
    TASK_TYPE_SUMMAIRZE_CONTEXT = 20 # 语义分析
    TASK_TYPE_TRANSLATE_SURFACE = 30 # 翻译词语
    TASK_TYPE_TRANSLATE_CONTEXT = 40 # 翻译上下文

    # 初始化请求配置参数
    LLMCONFIG = {}

    # 请求参数配置 - 判断词性
    LLMCONFIG[TASK_TYPE_ANALYZE_ATTRIBUTE] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_ANALYZE_ATTRIBUTE].TEMPERATURE = 0
    LLMCONFIG[TASK_TYPE_ANALYZE_ATTRIBUTE].TOP_P = 1
    LLMCONFIG[TASK_TYPE_ANALYZE_ATTRIBUTE].MAX_TOKENS = 512
    LLMCONFIG[TASK_TYPE_ANALYZE_ATTRIBUTE].FREQUENCY_PENALTY = 0

    # 请求参数配置 - 语义分析
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].TEMPERATURE = 0
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].TOP_P = 1
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].MAX_TOKENS = 512
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].FREQUENCY_PENALTY = 0

    # 请求参数配置 - 翻译词语
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].TEMPERATURE = 0
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].TOP_P = 1
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].MAX_TOKENS = 512
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].FREQUENCY_PENALTY = 0

    # 请求参数配置 - 翻译上下文
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].TEMPERATURE = 0
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].TOP_P = 1
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].MAX_TOKENS = 768
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].FREQUENCY_PENALTY = 0

    def __init__(self, config):
        # 初始化OpenAI API密钥、基础URL和模型名称
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.model_name = config.model_name
        
        # 初始化各类prompt和黑名单
        self.black_list = ""
        self.prompt_analyze_attribute = ""
        self.prompt_summarize_context = ""
        self.prompt_translate_surface = ""
        self.prompt_translate_context = ""

        # 请求限制器
        if config.request_frequency_threshold > 1:
            self.semaphore = asyncio.Semaphore(config.request_frequency_threshold)
            self.async_limiter = AsyncLimiter(max_rate = config.request_frequency_threshold, time_period = 1)
        elif config.request_frequency_threshold > 0:
            self.semaphore = asyncio.Semaphore(1)
            self.async_limiter = AsyncLimiter(max_rate = 1, time_period = 1 / config.request_frequency_threshold)
        else:
            self.semaphore = asyncio.Semaphore(1)
            self.async_limiter = AsyncLimiter(max_rate = 1, time_period = 1)

        # 初始化OpenAI客户端
        self.openai_handler = AsyncOpenAI(
            api_key = self.api_key,
            base_url = self.base_url if self.base_url.endswith("/v1") else self.base_url + "/v1",
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
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_analyze_attribute(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_analyze_attribute = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_summarize_context(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_summarize_context = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_translate_surface(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_translate_surface = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_translate_context(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_translate_context = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 异步发送请求到OpenAI获取模型回复
    async def request(self, prompt, content, task_type, retry = False):
        completion = await self.openai_handler.chat.completions.create(
            model = self.model_name,
            temperature = self.LLMCONFIG[task_type].TEMPERATURE,
            top_p = self.LLMCONFIG[task_type].TOP_P,
            max_tokens = self.LLMCONFIG[task_type].MAX_TOKENS,
            frequency_penalty = self.LLMCONFIG[task_type].FREQUENCY_PENALTY + 0.2 if retry else self.LLMCONFIG[task_type].FREQUENCY_PENALTY,
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
    async def analyze_attribute(self, word, retry):
        async with self.semaphore, self.async_limiter:
            prompt = self.prompt_analyze_attribute.replace("{surface}", word.surface)
            task_type = self.TASK_TYPE_ANALYZE_ATTRIBUTE
            usage, message, llmresponse = await self.request(prompt, "\n".join(word.context), task_type, retry)

            if usage.completion_tokens >= self.LLMCONFIG[task_type].MAX_TOKENS:
                raise Exception("usage.completion_tokens >= MAX_TOKENS")

            try:
                result = json.loads(
                    TextHelper.fix_broken_json_string(message.content.strip())
                )
            except Exception as e:
                LogHelper.debug(f"{e} + {LogHelper.get_trackback(e)}")
                LogHelper.debug(message.content.strip())
                LogHelper.debug(TextHelper.fix_broken_json_string(message.content.strip()))
                raise e

            if any(v in ["是", "は"] for v in result["character_name"]):
                word.type = Word.TYPE_PERSON
                LogHelper.debug(f"{word.surface} - {result}")
            elif "否" in result["character_name"]:
                word.type = Word.TYPE_NOT_PERSON
                LogHelper.info(f"[词性判断] 已剔除 - {word.surface} - {result}")
            else:
                raise Exception(f"不正确的返回值 - {word.surface} - {result["character_name"]}")
            
            return word

    # 词性判断任务完成时的回调
    def on_analyze_attribute_task_done(self, future, words, words_failed, words_successed):
        try:
            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[词性判断] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as e:
            LogHelper.warning(f"[词性判断] 子任务执行失败，稍后将重试 ... {e}")

    # 批量执行词性判断任务的具体实现
    async def do_analyze_attribute_batch(self, words, words_failed, words_successed):
        if len(words_failed) == 0:
            retry = False
            words_this_round = words
        else:
            retry = True
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.analyze_attribute(word, retry))
            task.add_done_callback(lambda future: self.on_analyze_attribute_task_done(future, words, words_failed, words_successed))
            tasks.append(task)

        # 等待异步任务完成 
        await asyncio.gather(*tasks, return_exceptions=True)

        # 获得失败任务的列表
        words_failed = [word_a for word_a in words if not any(word_a.surface == word_b.surface for word_b in words_successed)]

        return words_failed, words_successed

    # 批量执行词性判断任务
    async def analyze_attribute_batch(self, words):
        words_failed = []
        words_successed = []

        # 第一次请求
        words_failed, words_successed = await self.do_analyze_attribute_batch(words, words_failed, words_successed)

        # 开始重试流程
        for i in range(self.MAX_RETRY):
            if len(words_failed) > 0:
                LogHelper.warning( f"[词语词性] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                words_failed, words_successed = await self.do_analyze_attribute_batch(words, words_failed, words_successed)

        return words

    # 词语翻译任务
    async def translate_surface(self, word, retry):
        async with self.semaphore, self.async_limiter:
            prompt = self.prompt_translate_surface.replace("{attribute}", word.attribute)
            task_type = self.TASK_TYPE_TRANSLATE_SURFACE
            usage, message, llmresponse = await self.request(prompt, word.surface, task_type, retry)

            if usage.completion_tokens >= self.LLMCONFIG[task_type].MAX_TOKENS:
                raise Exception("usage.completion_tokens >= MAX_TOKENS")

            try:
                data = json.loads(
                    TextHelper.fix_broken_json_string(message.content.strip())
                )
            except Exception as error:
                LogHelper.debug(error)
                LogHelper.debug(word.surface)
                LogHelper.debug(message.content.strip())
                LogHelper.debug(TextHelper.fix_broken_json_string(message.content.strip()))
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
        async with self.semaphore, self.async_limiter:
            context_translation = []
            prompt = self.prompt_translate_context
            task_type = self.TASK_TYPE_TRANSLATE_CONTEXT
            usage, message, llmresponse = await self.request(prompt, "\n".join(word.context), task_type, retry)

            if usage.completion_tokens >= self.LLMCONFIG[task_type].MAX_TOKENS:
                raise Exception("usage.completion_tokens >= MAX_TOKENS")
            
            for k, line in enumerate(message.content.split("\n")):
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

    # 语义分析任务 
    async def summarize_context(self, word, retry):
        async with self.semaphore, self.async_limiter:
            prompt = self.prompt_summarize_context.replace("{surface}", word.surface)
            task_type = self.TASK_TYPE_SUMMAIRZE_CONTEXT
            usage, message, llmresponse = await self.request(prompt, "\n".join(word.context), task_type, retry)

            if usage.completion_tokens >= self.LLMCONFIG[task_type].MAX_TOKENS:
                raise Exception("usage.completion_tokens >= MAX_TOKENS")
    
            try:
                result = json.loads(
                    TextHelper.fix_broken_json_string(message.content.strip())
                )
            except Exception as e:
                LogHelper.debug(f"{e} + {LogHelper.get_trackback(e)}")
                LogHelper.debug(message.content.strip())
                LogHelper.debug(TextHelper.fix_broken_json_string(message.content.strip()))
                raise e

            if any(v in ["是", "は"] for v in result["character_name"]):
                word.type = Word.TYPE_PERSON
                LogHelper.debug(f"{word.surface} - {result}")
            elif "否" in result["character_name"]:
                word.type = Word.TYPE_NOT_PERSON
                LogHelper.info(f"[语义分析] 已剔除 - {word.surface} - {result}")
            else:
                raise Exception(f"不正确的返回值 - {word.surface} - {result["character_name"]}")

            word.attribute = result["sex"]
            word.context_summary = result

            return word

    # 语义分析任务完成时的回调
    def on_summarize_context_task_done(self, future, words, words_failed, words_successed):
        try:
            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[语义分析] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as e:
            LogHelper.warning(f"[语义分析] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")

    # 批量执行语义分析任务的具体实现
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

    # 批量执行语义分析任务
    async def summarize_context_batch(self, words):
        words_failed = []
        words_successed = []

        # 第一次请求
        words_failed, words_successed = await self.do_summarize_context_batch(words, words_failed, words_successed)

        # 开始重试流程
        for i in range(self.MAX_RETRY):
            if len(words_failed) > 0:
                LogHelper.warning( f"[语义分析] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                words_failed, words_successed = await self.do_summarize_context_batch(words, words_failed, words_successed)

        return words