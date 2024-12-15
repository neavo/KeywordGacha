import os
import json
import asyncio
import urllib.request
from types import SimpleNamespace
from concurrent.futures import Future

import pykakasi
from openai import AsyncOpenAI
from aiolimiter import AsyncLimiter

from model.Word import Word
from module.LogHelper import LogHelper
from module.TextHelper import TextHelper

class LLMConfig():

    TEMPERATURE = 0.05
    TOP_P = 0.85
    MAX_TOKENS = 768
    FREQUENCY_PENALTY = 0

class ProcessMode():

    NORMAL = 1
    QUICK = 2

class LLM:

    MAX_RETRY = 3 # 最大重试次数

    TASK_TYPE_API_TEST = 10             # 语义分析
    TASK_TYPE_SUMMAIRZE_CONTEXT = 20    # 语义分析
    TASK_TYPE_TRANSLATE_SURFACE = 30    # 翻译词语
    TASK_TYPE_TRANSLATE_CONTEXT = 40    # 翻译上下文

    # 处理模式
    PROCESS_MODE = ProcessMode()

    # 初始化请求配置参数
    LLMCONFIG: dict[int, LLMConfig] = {}

    # 请求参数配置 - 接口测试
    LLMCONFIG[TASK_TYPE_API_TEST] = LLMConfig()
    LLMCONFIG[TASK_TYPE_API_TEST].TEMPERATURE = 0.05
    LLMCONFIG[TASK_TYPE_API_TEST].TOP_P = 0.85
    LLMCONFIG[TASK_TYPE_API_TEST].MAX_TOKENS = 768
    LLMCONFIG[TASK_TYPE_API_TEST].FREQUENCY_PENALTY = 0

    # 请求参数配置 - 语义分析
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT] = LLMConfig()
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].TEMPERATURE = 0.05
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].TOP_P = 0.85
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].MAX_TOKENS = 768
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].FREQUENCY_PENALTY = 0

    # 请求参数配置 - 翻译词语
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE] = LLMConfig()
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].TEMPERATURE = 0.05
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].TOP_P = 0.85
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].MAX_TOKENS = 768
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].FREQUENCY_PENALTY = 0

    # 请求参数配置 - 翻译上下文
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT] = LLMConfig()
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].TEMPERATURE = 0.75
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].TOP_P = 0.95
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].MAX_TOKENS = 1024
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].FREQUENCY_PENALTY = 0

    # 角色实体关键词
    PER_KEYWORD = (
        "人名",
        "名字",
        "姓氏",
        "姓名",
        "昵称",
        "角色",
        "人物",
    )

    def __init__(self, config: SimpleNamespace) -> None:
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

    # 设置语言
    def set_language(self, language: int) -> None:
        self.language = language

    # 加载 Prompt 文件内容
    def load_prompt(self) -> None:
        try:
            for entry in os.scandir("prompt"):
                if entry.is_file() and "prompt" in entry.name and entry.name.endswith(".txt"):
                    with open(entry.path, "r", encoding = "utf-8") as reader:
                        setattr(self, entry.name.replace(".txt", ""), reader.read().strip())
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 检查词语的描述是否包含特定关键词
    def check_keyword_in_description(self, word: Word, keywords: tuple) -> bool:
        return any(keyword in word.surface_translation_description for keyword in keywords)

    # 异步发送请求到 OpenAI 获取模型回复
    async def do_request(self, messages: list, task_type: int, retry: bool) -> tuple[dict, dict, dict, dict, Exception]:
        try:
            usage, message, llm_request, llm_response, error = None, None, None, None, None

            llm_request = {
                "model" : self.model_name,
                "stream" : False,
                "temperature" : self.LLMCONFIG[task_type].TEMPERATURE,
                "top_p" : self.LLMCONFIG[task_type].TOP_P,
                "max_tokens" : self.LLMCONFIG[task_type].MAX_TOKENS,
                "frequency_penalty" : self.LLMCONFIG[task_type].FREQUENCY_PENALTY + 0.2 if retry else self.LLMCONFIG[task_type].FREQUENCY_PENALTY,
                "messages" : messages,
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
    def set_request_limiter(self) -> None:
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
                    LogHelper.info("")
                    LogHelper.info(f"检查到 [green]llama.cpp[/]，根据其配置，请求频率阈值自动设置为 [green]{len(data)}[/] 次/秒 ...")
                    LogHelper.info("")
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
    async def api_test(self) -> bool:
        async with self.semaphore, self.async_limiter:
            try:
                result = False

                usage, message, llm_request, llm_response, error = await self.do_request(
                    [
                        {
                            "role": "user",
                            "content": (
                                self.prompt_translate_surface
                                    .replace("{surface}", "ダリヤ")
                                    .replace("{context}", "魔導具師ダリヤはうつむかない")
                            ),
                        },
                    ],
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
    async def translate_surface(self, word: Word, words: list[Word], failure: list[Word], success: list[Word], retry: bool) -> None:
        async with self.semaphore, self.async_limiter:
            try:
                usage, message, llm_request, llm_response, error = await self.do_request(
                    [
                        {
                            "role": "user",
                            "content": (
                                self.prompt_translate_surface
                                    .replace("{surface}", word.surface)
                                    .replace("{context}", word.get_context_str_for_surface_translate())
                            ),
                        },
                    ],
                    self.TASK_TYPE_TRANSLATE_SURFACE,
                    retry
                )

                if error != None:
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
                if self.check_keyword_in_description(word, ("语气词", "拟声词", "感叹词", "形容词")):
                    word.type = ""
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
                if error != None:
                    failure.append(word)
                else:
                    success.append(word)
                    LogHelper.info(f"[词语翻译] 已完成 {len(success)} / {len(words)} ...")

    # 批量执行词语翻译任务
    async def translate_surface_batch(self, words: list[Word]) -> list[Word]:
        failure = []
        success = []

        for i in range(self.MAX_RETRY + 1):
            if i == 0:
                retry = False
                words_this_round = words
            elif len(failure) > 0:
                retry = True
                words_this_round = failure
                LogHelper.warning(f"[词语翻译] 即将开始第 {i} / {self.MAX_RETRY} 轮重试...")
            else:
                break

            # 执行异步任务
            tasks = [
                asyncio.create_task(self.translate_surface(word, words, failure, success, retry))
                for word in words_this_round
            ]
            await asyncio.gather(*tasks, return_exceptions = True)

        return words

    # 上下文翻译任务
    async def translate_context(self, word: Word, words: list[Word], failure: list[Word], success: list[Word], retry: bool) -> None:
        async with self.semaphore, self.async_limiter:
            try:
                usage, message, llm_request, llm_response, error = await self.do_request(
                    [
                        {
                            "role": "user",
                            "content": (
                                self.prompt_translate_context
                                    .replace("{context}", word.get_context_str_for_translate(self.language))
                            ),
                        },
                    ],
                    self.TASK_TYPE_TRANSLATE_CONTEXT,
                    retry
                )

                if error:
                    raise error

                if usage.completion_tokens >= self.LLMCONFIG[self.TASK_TYPE_TRANSLATE_CONTEXT].MAX_TOKENS:
                    raise Exception("usage.completion_tokens >= MAX_TOKENS")

                context_translation = [line.strip() for line in message.content.split("\n") if line.strip() != ""]

                word.context_translation = context_translation
                word.llmresponse_translate_context = llm_response
            except Exception as e:
                LogHelper.warning(f"[上下文翻译] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")
                LogHelper.debug(f"llm_request - {llm_request}")
                LogHelper.debug(f"llm_response - {llm_response}")
                error = e
            finally:
                if error != None:
                    failure.append(word)
                else:
                    success.append(word)
                    LogHelper.info(f"[上下文翻译] 已完成 {len(success)} / {len(words)} ...")

    # 批量执行上下文翻译任务
    async def translate_context_batch(self, words: list[Word]) -> list[Word]:
        failure = []
        success = []

        for i in range(self.MAX_RETRY + 1):
            if i == 0:
                retry = False
                words_this_round = words
            elif len(failure) > 0:
                retry = True
                words_this_round = failure
                LogHelper.warning(f"[上下文翻译] 即将开始第 {i} / {self.MAX_RETRY} 轮重试...")
            else:
                break

            # 执行异步任务
            tasks = [
                asyncio.create_task(self.translate_context(word, words, failure, success, retry))
                for word in words_this_round
            ]
            await asyncio.gather(*tasks, return_exceptions = True)

        return words

    # 语义分析任务
    async def summarize_context(self, word: Word, words: list[Word], failure: list[Word], success: list[Word], mode: int, retry: bool) -> None:
        async with self.semaphore, self.async_limiter:
            try:
                error = None

                if mode == LLM.PROCESS_MODE.QUICK:
                    word.type = "" if not self.check_keyword_in_description(word, LLM.PER_KEYWORD) else word.type
                else:
                    usage, message, llm_request, llm_response, error = await self.do_request(
                        [
                            {
                                "role": "user",
                                "content": (
                                    self.prompt_summarize_context
                                        .replace("{surface}", word.surface)
                                        .replace("{context}", word.get_context_str_for_summarize(self.language))
                                ),
                            },
                        ],
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
                        word.type = ""
                        LogHelper.info(f"[语义分析] 已剔除 - {word.surface} - {result}")

                    word.gender = result.get("gender", "").strip()
                    word.context_summary = result.get("summary", "").strip()
                    word.llmresponse_summarize_context = llm_response
            except Exception as e:
                LogHelper.warning(f"[语义分析] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")
                LogHelper.debug(f"llm_request - {llm_request}")
                LogHelper.debug(f"llm_response - {llm_response}")
                error = e
            finally:
                if error != None:
                    failure.append(word)
                else:
                    success.append(word)
                    LogHelper.info(f"[语义分析] 已完成 {len(success)} / {len(words)} ...")

    # 批量执行语义分析任务
    async def summarize_context_batch(self, words: list[Word], mode: int) -> list[Word]:
        failure = []
        success = []

        for i in range(self.MAX_RETRY + 1):
            if i == 0:
                retry = False
                words_this_round = words
            elif len(failure) > 0:
                retry = True
                words_this_round = failure
                LogHelper.warning(f"[语义分析] 即将开始第 {i} / {self.MAX_RETRY} 轮重试...")
            else:
                break

            # 执行异步任务
            tasks = [
                asyncio.create_task(self.summarize_context(word, words, failure, success, mode, retry))
                for word in words_this_round
            ]
            await asyncio.gather(*tasks, return_exceptions = True)

        return words