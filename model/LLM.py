import os
import re
import json
import asyncio
import threading
import urllib.request
from types import SimpleNamespace

import pykakasi
from openai import AsyncOpenAI
from aiolimiter import AsyncLimiter

from model.NER import NER
from model.Word import Word
from module.LogHelper import LogHelper
from module.TextHelper import TextHelper

class LLM:

    # 任务类型
    class Type():

        API_TEST = 100                  # 语义分析
        SURFACE_ANALYSIS = 200          # 语义分析
        TRANSLATE_CONTEXT = 300         # 翻译上下文

    # LLM 配置参数
    class LLMConfig():

        TEMPERATURE = 0.05
        TOP_P = 0.85
        MAX_TOKENS = 768
        FREQUENCY_PENALTY = 0

    # 最大重试次数
    MAX_RETRY = 3

    # 请求参数配置 - 接口测试
    API_TEST_CONFIG = LLMConfig()
    API_TEST_CONFIG.TEMPERATURE = 0.05
    API_TEST_CONFIG.TOP_P = 0.85
    API_TEST_CONFIG.MAX_TOKENS = 768
    API_TEST_CONFIG.FREQUENCY_PENALTY = 0

    # 请求参数配置 - 词义分析
    SURFACE_ANALYSIS_CONFIG = LLMConfig()
    SURFACE_ANALYSIS_CONFIG.TEMPERATURE = 0.05
    SURFACE_ANALYSIS_CONFIG.TOP_P = 0.85
    SURFACE_ANALYSIS_CONFIG.MAX_TOKENS = 768
    SURFACE_ANALYSIS_CONFIG.FREQUENCY_PENALTY = 0

    # 请求参数配置 - 翻译上下文
    TRANSLATE_CONTEXT_CONFIG = LLMConfig()
    TRANSLATE_CONTEXT_CONFIG.TEMPERATURE = 0.95
    TRANSLATE_CONTEXT_CONFIG.TOP_P = 0.85
    TRANSLATE_CONTEXT_CONFIG.MAX_TOKENS = 768
    TRANSLATE_CONTEXT_CONFIG.FREQUENCY_PENALTY = 0

    def __init__(self, config: SimpleNamespace) -> None:
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.model_name = config.model_name
        self.request_timeout = config.request_timeout
        self.request_frequency_threshold = config.request_frequency_threshold

        # 初始化
        self.kakasi = pykakasi.kakasi()
        self.client = self.load_client()

        # 线程锁
        self.lock = threading.Lock()

    # 初始化 OpenAI 客户端
    def load_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
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

    # 设置请求限制器
    def set_request_limiter(self) -> None:
            # 获取 llama.cpp 响应数据
            try:
                response_json = None
                with urllib.request.urlopen(f"{re.sub(r"/v1$", "", self.base_url)}/slots") as response:
                    response_json = json.loads(response.read().decode("utf-8"))
            except Exception:
                LogHelper.debug("无法获取 [green]llama.cpp[/] 响应数据 ...")

            # 如果响应数据有效，则设置请求频率阈值为 slots 数量
            if isinstance(response_json, list) and len(response_json) > 0:
                self.request_frequency_threshold = len(response_json)
                LogHelper.info("")
                LogHelper.info(f"检查到 [green]llama.cpp[/]，根据其配置，请求频率阈值自动设置为 [green]{len(response_json)}[/] 次/秒 ...")
                LogHelper.info("")

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

    # 异步发送请求到 OpenAI 获取模型回复
    async def do_request(self, messages: list, llm_config: LLMConfig, retry: bool) -> tuple[dict, dict, dict, dict, Exception]:
        try:
            usage, message, llm_request, llm_response, error = None, None, None, None, None

            llm_request = {
                "model" : self.model_name,
                "stream" : False,
                "temperature" : llm_config.TEMPERATURE,
                "top_p" : llm_config.TOP_P,
                "max_tokens" : llm_config.MAX_TOKENS,
                "max_completion_tokens" : llm_config.MAX_TOKENS,
                "frequency_penalty" : llm_config.FREQUENCY_PENALTY + 0.2 if retry == True else llm_config.FREQUENCY_PENALTY,
                "messages" : messages,
            }

            completion = await self.client.chat.completions.create(**llm_request)

            # OpenAI 的 API 返回的对象通常是 OpenAIObject 类型
            # 该类有一个内置方法可以将其转换为字典
            llm_response = completion.to_dict()
            usage = completion.usage
            message = completion.choices[0].message
        except Exception as e:
            error = e
        finally:
            return usage, message, llm_request, llm_response, error


    # 接口测试任务
    async def api_test(self) -> bool:
        async with self.semaphore, self.async_limiter:
            try:
                success = False

                usage, message, llm_request, llm_response, error = await self.do_request(
                    [
                        {
                            "role": "system",
                            "content": self.prompt_surface_analysis_with_translation,
                        },
                        {
                            "role": "user",
                            "content": (
                                "目标词语：ダリヤ"
                                + "\n" + "参考文本：\n魔導具師ダリヤはうつむかない"
                            ),
                        },
                    ],
                    LLM.API_TEST_CONFIG,
                    True
                )

                # 检查错误
                if error != None:
                    raise error

                # 检查是否超过最大 token 限制
                if usage.completion_tokens >= LLM.API_TEST_CONFIG.MAX_TOKENS:
                    raise Exception("模型发生退化 ...")

                # 反序列化 JSON
                result = TextHelper.safe_load_json_dict(message.content.strip())
                if len(result) == 0:
                    raise Exception("反序列化失败 ...")

                # 输出结果
                success = True
                LogHelper.info(f"{result}")

                return success
            except Exception as e:
                LogHelper.warning(f"{LogHelper.get_trackback(e)}")
                LogHelper.warning(f"llm_request - {llm_request}")
                LogHelper.warning(f"llm_response - {llm_response}")

    # 词义分析任务
    async def surface_analysis(self, word: Word, words: list[Word], success: list[Word], retry: bool) -> None:
        async with self.semaphore, self.async_limiter:
            try:
                if self.language != NER.Language.ZH:
                    prompt = self.prompt_surface_analysis_with_translation
                else:
                    prompt = self.prompt_surface_analysis_without_translation

                usage, message, llm_request, llm_response, error = await self.do_request(
                    [
                        {
                            "role": "system",
                            "content": prompt,
                        },
                        {
                            "role": "user",
                            "content": (
                                f"目标词语：{word.surface}"
                                + "\n" + f"参考文本：\n{word.get_context_str_for_surface_analysis(self.language)}"
                            ),
                        },
                    ],
                    LLM.SURFACE_ANALYSIS_CONFIG,
                    retry
                )

                # 检查错误
                if error != None:
                    raise error

                # 检查是否超过最大 token 限制
                if usage.completion_tokens >= LLM.SURFACE_ANALYSIS_CONFIG.MAX_TOKENS:
                    raise Exception("模型发生退化 ...")

                # 反序列化 JSON
                result = TextHelper.safe_load_json_dict(message.content.strip())
                if len(result) == 0:
                    raise Exception("反序列化失败 ...")

                # 获取结果
                word.gender = result.get("gender", "").replace("性别判断：", "").strip()
                word.context_summary = result.get("summary", "").replace("故事梗概：", "").strip()
                word.surface_translation = result.get("translation", "").replace("翻译结果：", "").strip()
                word.surface_translation_description = result.get("analysis", "").replace("特征分析：", "").strip()
                word.llmrequest_surface_analysis = llm_request
                word.llmresponse_surface_analysis = llm_response

                if any(v for v in ("姓名", "家族") if v in result.get("entity_type", "")):
                    if word.type != "PER":
                        LogHelper.info(f"[词义分析] 类型修正（{word.type} -> PER） - {word.surface} - {result}")
                        word.type = "PER"
                elif "组织" in result.get("entity_type", ""):
                    if word.type != "ORG":
                        LogHelper.info(f"[词义分析] 类型修正（{word.type} -> ORG） - {word.surface} - {result}")
                        word.type = "ORG"
                elif "地点" in result.get("entity_type", ""):
                    if word.type != "LOC":
                        LogHelper.info(f"[词义分析] 类型修正（{word.type} -> LOC） - {word.surface} - {result}")
                        word.type = "LOC"
                elif "物品" in result.get("entity_type", ""):
                    if word.type != "PRD":
                        LogHelper.info(f"[词义分析] 类型修正（{word.type} -> PRD） - {word.surface} - {result}")
                        word.type = "PRD"
                elif "事件" in result.get("entity_type", ""):
                    if word.type != "EVT":
                        LogHelper.info(f"[词义分析] 类型修正（{word.type} -> EVT） - {word.surface} - {result}")
                        word.type = "EVT"
                else:
                    LogHelper.info(f"[词义分析] 已剔除 - {word.type} - {word.surface} - {result}")
                    word.type = ""

                # 生成罗马音，汉字有时候会生成重复的罗马音，所以需要去重
                results = list(set([item.get("hepburn", "") for item in self.kakasi.convert(word.surface)]))
                word.surface_romaji = (" ".join(results)).strip()
            except Exception as e:
                LogHelper.warning(f"[词义分析] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")
                LogHelper.debug(f"llm_request - {llm_request}")
                LogHelper.debug(f"llm_response - {llm_response}")
                error = e
            finally:
                if error == None:
                    with self.lock:
                        success.append(word)
                    LogHelper.info(f"[词义分析] 已完成 {len(success)} / {len(words)} ...")

    # 批量执行词义分析任务
    async def surface_analysis_batch(self, words: list[Word]) -> list[Word]:
        failure = []
        success = []

        for i in range(self.MAX_RETRY + 1):
            if i == 0:
                retry = False
                words_this_round = words
            elif len(failure) > 0:
                retry = True
                words_this_round = failure
                LogHelper.warning(f"[词义分析] 即将开始第 {i} / {self.MAX_RETRY} 轮重试...")
            else:
                break

            # 执行异步任务
            tasks = [
                asyncio.create_task(self.surface_analysis(word, words, success, retry))
                for word in words_this_round
            ]
            await asyncio.gather(*tasks, return_exceptions = True)

            # 获得失败任务的列表
            success_pairs = {(word.surface, word.type) for word in success}
            failure = [word for word in words if (word.surface, word.type) not in success_pairs]

        return words

    # 上下文翻译任务
    async def context_translate(self, word: Word, words: list[Word], success: list[Word], retry: bool) -> None:
        async with self.semaphore, self.async_limiter:
            try:
                usage, message, llm_request, llm_response, error = await self.do_request(
                    [
                        {
                            "role": "system",
                            "content": self.prompt_context_translate,
                        },
                        {
                            "role": "user",
                            "content": f"轻小说文本：\n{word.get_context_str_for_translate(self.language)}",
                        },
                    ],
                    LLM.TRANSLATE_CONTEXT_CONFIG,
                    retry
                )

                if error != None:
                    raise error

                if usage.completion_tokens >= LLM.TRANSLATE_CONTEXT_CONFIG.MAX_TOKENS:
                    raise Exception("模型发生退化 ...")

                context_translation = [line.strip() for line in message.content.splitlines() if line.strip() != ""]

                word.context_translation = context_translation
                word.llmrequest_context_translate = llm_request
                word.llmresponse_context_translate = llm_response
            except Exception as e:
                LogHelper.warning(f"[上下文翻译] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")
                LogHelper.debug(f"llm_request - {llm_request}")
                LogHelper.debug(f"llm_response - {llm_response}")
                error = e
            finally:
                if error == None:
                    with self.lock:
                        success.append(word)
                    LogHelper.info(f"[上下文翻译] 已完成 {len(success)} / {len(words)} ...")

    # 批量执行上下文翻译任务
    async def context_translate_batch(self, words: list[Word]) -> list[Word]:
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
                asyncio.create_task(self.context_translate(word, words, success, retry))
                for word in words_this_round
            ]
            await asyncio.gather(*tasks, return_exceptions = True)

            # 获得失败任务的列表
            success_pairs = {(word.surface, word.type) for word in success}
            failure = [word for word in words if (word.surface, word.type) not in success_pairs]

        return words