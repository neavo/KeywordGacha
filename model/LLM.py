import re
import json
import random
import asyncio
import urllib.request
from concurrent.futures import Future

import pykakasi
from openai import AsyncOpenAI
from aiolimiter import AsyncLimiter

from model.NER import NER
from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

class LLM:

    MAX_RETRY = 3 # 最大重试次数

    TASK_TYPE_API_TEST = 10             # 语义分析
    TASK_TYPE_SUMMAIRZE_CONTEXT = 20    # 语义分析
    TASK_TYPE_TRANSLATE_SURFACE = 30    # 翻译词语
    TASK_TYPE_TRANSLATE_CONTEXT = 40    # 翻译上下文

    # 处理模式
    PROCESS_MODE = type("GClass", (), {})()
    PROCESS_MODE.NORMAL = 1
    PROCESS_MODE.QUICK = 2

    # 初始化请求配置参数
    LLMCONFIG = {}

    # 请求参数配置 - 接口测试
    LLMCONFIG[TASK_TYPE_API_TEST] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_API_TEST].TEMPERATURE = 0.05
    LLMCONFIG[TASK_TYPE_API_TEST].TOP_P = 0.85
    LLMCONFIG[TASK_TYPE_API_TEST].MAX_TOKENS = 768
    LLMCONFIG[TASK_TYPE_API_TEST].FREQUENCY_PENALTY = 0

    # 请求参数配置 - 语义分析
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].TEMPERATURE = 0.05
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].TOP_P = 0.85
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].MAX_TOKENS = 768
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].FREQUENCY_PENALTY = 0

    # 请求参数配置 - 翻译词语
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].TEMPERATURE = 0.05
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].TOP_P = 0.85
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].MAX_TOKENS = 768
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].FREQUENCY_PENALTY = 0

    # 请求参数配置 - 翻译上下文
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].TEMPERATURE = 0.75
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].TOP_P = 0.95
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].MAX_TOKENS = 1024
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].FREQUENCY_PENALTY = 0
    
    def __init__(self, config):
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.model_name = config.model_name
        self.request_timeout = config.request_timeout
        self.request_frequency_threshold = config.request_frequency_threshold

        # 初始化 pykakasi
        self.kakasi = pykakasi.kakasi()

        # 初始化OpenAI客户端
        self.openai_handler = AsyncOpenAI(
            timeout = self.request_timeout,
            api_key = self.api_key,
            base_url = self.base_url,
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
    def load_prompt_summarize_context(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_summarize_context = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_translate_context(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_translate_context = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_translate_surface(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_translate_surface = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 检查词语的描述是否包含特定关键词
    def check_keyword_in_description(self, word: Word, keywords: list[str] = ["人名", "名字", "姓氏", "姓名", "名称", "昵称", "角色名"]):
        return any(keyword in word.surface_translation_description for keyword in keywords)

    # 异步发送请求到OpenAI获取模型回复
    async def request(self, content, task_type, retry = False):     
        try:
            usage, message, llm_request, llm_response, error = None, None, None, None, None

            llm_request = {
                "model" : self.model_name,
                "stream" : False,
                "temperature" : self.LLMCONFIG[task_type].TEMPERATURE,
                "top_p" : self.LLMCONFIG[task_type].TOP_P,
                "max_tokens" : self.LLMCONFIG[task_type].MAX_TOKENS,
                "frequency_penalty" : self.LLMCONFIG[task_type].FREQUENCY_PENALTY + 0.2 if retry else self.LLMCONFIG[task_type].FREQUENCY_PENALTY,
                "messages" : [
                    {
                        "role": "user", 
                        "content": content
                    },
                ],
            }
            
            completion = await self.openai_handler.chat.completions.create(**llm_request)

            llm_response = completion
            usage = completion.usage
            message = completion.choices[0].message
        except Exception as e:
            error = e
        finally:
            return usage, message, llm_request, llm_response, error

    # 设置请求限制器
    def set_request_limiter(self):
            try:
                num = -1
                url = self.base_url.replace("/v1", "") if self.base_url.endswith("/v1") else self.base_url
                with urllib.request.urlopen(f"{url}/slots") as response:
                    data = json.loads(response.read().decode("utf-8"))
                    num = len(data) if data != None and len(data) > 0 else num
            except Exception as e:
                LogHelper.debug(f"{LogHelper.get_trackback(e)}")
            finally:
                if num > 0:
                    LogHelper.info(f"")
                    LogHelper.info(f"检查到 [green]llama.cpp[/]，根据其配置，请求频率阈值自动设置为 [green]{len(data)}[/] 次/秒 ...")
                    LogHelper.info(f"")
                    self.request_frequency_threshold = len(data)

                # 设置请求限制器
                if self.request_frequency_threshold > 1:
                    self.semaphore = asyncio.Semaphore(self.request_frequency_threshold)
                    self.async_limiter = AsyncLimiter(max_rate = self.request_frequency_threshold, time_period = 1)
                elif self.request_frequency_threshold > 0:
                    self.semaphore = asyncio.Semaphore(1)
                    self.async_limiter = AsyncLimiter(max_rate = 1, time_period = 1 / self.request_frequency_threshold)
                else:
                    self.semaphore = asyncio.Semaphore(1)
                    self.async_limiter = AsyncLimiter(max_rate = 1, time_period = 1)

    # 接口测试任务
    async def api_test(self):
        async with self.semaphore, self.async_limiter:
            try:
                result = False

                usage, message, llm_request, llm_response, error = await self.request(
                    self.prompt_translate_surface.replace("{surface}", "ダリヤ").replace("{context}", "魔導具師ダリヤはうつむかない"),
                    self.TASK_TYPE_API_TEST,
                    True
                )

                if error:
                    raise error

                if usage.completion_tokens >= self.LLMCONFIG[self.TASK_TYPE_API_TEST].MAX_TOKENS:
                    raise Exception("usage.completion_tokens >= MAX_TOKENS")                
            
                data = json.loads(
                    TextHelper.fix_broken_json_string(message.content.strip())
                )

                result = True
                LogHelper.info(f"{data}")

                return result
            except Exception as e:
                LogHelper.warning(f"{LogHelper.get_trackback(e)}")
                LogHelper.warning(f"llm_request - {llm_request}")
                LogHelper.warning(f"llm_response - {llm_response}")

    # 词语翻译任务
    async def translate_surface(self, word: Word, retry: bool):
        async with self.semaphore, self.async_limiter:
            try:
                prompt = self.prompt_translate_surface.replace("{surface}", word.surface)
                prompt = prompt.replace("{context}", "\n".join(word.clip_context(256)))

                usage, message, llm_request, llm_response, error = await self.request(
                    prompt,
                    self.TASK_TYPE_TRANSLATE_SURFACE,
                    retry
                )

                if error:
                    raise error

                if usage.completion_tokens >= self.LLMCONFIG[self.TASK_TYPE_TRANSLATE_SURFACE].MAX_TOKENS:
                    raise Exception("usage.completion_tokens >= MAX_TOKENS")

                data = json.loads(
                    TextHelper.fix_broken_json_string(message.content.strip())
                )

                # 获取结果
                word.surface_translation = data.get("translation", "").strip()
                word.surface_translation_description = data.get("description", "").strip()
                word.llmresponse_translate_surface = llm_response

                # 检查词语描述种是否包含不应包含的关键字，如果包含则移除
                # 只检查描述不为空的非角色实体
                if (
                    word.ner_type != "PER"
                    and word.surface_translation_description != ""
                    and self.check_keyword_in_description(word, ["语气词", "拟声词", "感叹词", "形容词"])
                ):
                    word.ner_type = ""
                    LogHelper.debug(f"[词语翻译] 已剔除 - {word.surface} - {word.surface_translation_description}")

                # 生成罗马音，汉字有时候会生成重复的罗马音，所以需要去重
                results = list(set([item.get("hepburn", "") for item in self.kakasi.convert(word.surface)]))
                word.surface_romaji = (" ".join(results)).strip()
            except Exception as e:
                LogHelper.warning(f"[词语翻译] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")
                LogHelper.debug(f"llm_request - {llm_request}")
                LogHelper.debug(f"llm_response - {llm_response}")
                error = e
            finally:
                return error if error else word

    # 词语翻译任务完成时的回调
    def on_translate_surface_task_done(self, future, words, words_failed, words_successed):
        result = future.result()

        if not isinstance(result, Exception):
            words_successed.append(result)
            LogHelper.info(f"[词语翻译] 已完成 {len(words_successed)} / {len(words)} ...")

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

        # 等待异步任务完成 
        await asyncio.gather(*tasks, return_exceptions = True)

        # 获得失败任务的列表
        successed_word_pairs = {(word.surface, word.ner_type) for word in words_successed}
        words_failed = [word for word in words if (word.surface, word.ner_type) not in successed_word_pairs]

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
            try:
                usage, message, llm_request, llm_response, error = await self.request(
                    self.prompt_translate_context.replace("{context}", "\n".join(word.context)),
                    self.TASK_TYPE_TRANSLATE_CONTEXT,
                    retry
                )

                if error:
                    raise error

                if usage.completion_tokens >= self.LLMCONFIG[self.TASK_TYPE_TRANSLATE_CONTEXT].MAX_TOKENS:
                    raise Exception("usage.completion_tokens >= MAX_TOKENS")
                
                context_translation = []
                for k, line in enumerate(message.content.split("\n")):
                    if len(line) > 0:
                        context_translation.append(line)

                word.context_translation = context_translation
                word.llmresponse_translate_context = llm_response
            except Exception as e:
                LogHelper.warning(f"[上下文翻译] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")
                LogHelper.debug(f"llm_request - {llm_request}")
                LogHelper.debug(f"llm_response - {llm_response}")
                error = e
            finally:
                return error if error else word

    # 上下文翻译任务完成时的回调
    def on_translate_context_task_done(self, future, words, words_failed, words_successed):
        result = future.result()

        if not isinstance(result, Exception):
            words_successed.append(result)
            LogHelper.info(f"[上下文翻译] 已完成 {len(words_successed)} / {len(words)} ...")

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

        # 等待异步任务完成 
        await asyncio.gather(*tasks, return_exceptions = True)

        # 获得失败任务的列表
        successed_word_pairs = {(word.surface, word.ner_type) for word in words_successed}
        words_failed = [word for word in words if (word.surface, word.ner_type) not in successed_word_pairs]

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
    async def summarize_context(self, word: Word, retry: bool, mode: int):
        async with self.semaphore, self.async_limiter:
            try:
                error = None

                if mode == LLM.PROCESS_MODE.QUICK:
                    word.ner_type = "" if not self.check_keyword_in_description(word) else word.ner_type
                else:
                    usage, message, llm_request, llm_response, error = await self.request(
                        self.prompt_summarize_context.replace("{surface}", word.surface).replace("{context}", "\n".join(word.context)),
                        self.TASK_TYPE_SUMMAIRZE_CONTEXT,
                        retry
                    )

                    if error:
                        raise error

                    if usage.completion_tokens >= self.LLMCONFIG[self.TASK_TYPE_SUMMAIRZE_CONTEXT].MAX_TOKENS:
                        raise Exception("usage.completion_tokens >= MAX_TOKENS")

                    result = json.loads(
                        TextHelper.fix_broken_json_string(message.content.strip())
                    )

                    if "否" not in result.get("is_name", ""):
                        LogHelper.debug(f"[语义分析] 已完成 - {word.surface} - {result}")
                    else:
                        word.ner_type = ""
                        LogHelper.info(f"[语义分析] 已剔除 - {word.surface} - {result}")

                    word.attribute = result.get("gender", "").strip()
                    word.context_summary = result.get("summary", "").strip()
                    word.llmresponse_summarize_context = llm_response
            except Exception as e:
                LogHelper.warning(f"[语义分析] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")
                LogHelper.debug(f"llm_request - {llm_request}")
                LogHelper.debug(f"llm_response - {llm_response}")
                error = e
            finally:
                return error if error else word

    # 语义分析任务完成时的回调
    def on_summarize_context_task_done(self, future: Future, words: list[Word], words_failed: list[Word], words_successed: list[Word]):
        result = future.result()

        if not isinstance(result, Exception):
            words_successed.append(result)
            LogHelper.info(f"[语义分析] 已完成 {len(words_successed)} / {len(words)} ...")

    # 批量执行语义分析任务的具体实现
    async def do_summarize_context_batch(self, words: list[Word], words_failed: list[Word], words_successed: list[Word], mode: int):
        if len(words_failed) == 0:
            retry = False
            words_this_round = words
        else:
            retry = True
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.summarize_context(word, retry, mode))
            task.add_done_callback(lambda future: self.on_summarize_context_task_done(future, words, words_failed, words_successed))
            tasks.append(task)

        # 等待异步任务完成 
        await asyncio.gather(*tasks, return_exceptions = True)

        # 获得失败任务的列表
        successed_word_pairs = {(word.surface, word.ner_type) for word in words_successed}
        words_failed = [word for word in words if (word.surface, word.ner_type) not in successed_word_pairs]

        return words_failed, words_successed

    # 批量执行语义分析任务
    async def summarize_context_batch(self, words: list[Word], mode: int):
        words_failed = []
        words_successed = []

        # 第一次请求
        words_failed, words_successed = await self.do_summarize_context_batch(words, words_failed, words_successed, mode)

        # 开始重试流程
        for i in range(self.MAX_RETRY):
            if len(words_failed) > 0:
                LogHelper.warning( f"[语义分析] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                words_failed, words_successed = await self.do_summarize_context_batch(words, words_failed, words_successed, mode)

        return words 