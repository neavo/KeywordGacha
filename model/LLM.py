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
        TRANSLATE_CONTEXT = 300         # 翻译参考文本

    # LLM 配置参数
    class LLMConfig():

        TEMPERATURE = 0.05
        TOP_P = 0.95
        MAX_TOKENS = 1024
        FREQUENCY_PENALTY = 0

    # 最大重试次数
    MAX_RETRY = 3

    # 请求参数配置 - 接口测试
    API_TEST_CONFIG = LLMConfig()
    API_TEST_CONFIG.TEMPERATURE = 0.05
    API_TEST_CONFIG.TOP_P = 0.95
    API_TEST_CONFIG.MAX_TOKENS = 1024
    API_TEST_CONFIG.FREQUENCY_PENALTY = 0

    # 请求参数配置 - 词义分析
    SURFACE_ANALYSIS_CONFIG = LLMConfig()
    SURFACE_ANALYSIS_CONFIG.TEMPERATURE = 0.05
    SURFACE_ANALYSIS_CONFIG.TOP_P = 0.95
    SURFACE_ANALYSIS_CONFIG.MAX_TOKENS = 1024
    SURFACE_ANALYSIS_CONFIG.FREQUENCY_PENALTY = 0

    # 请求参数配置 - 翻译参考文本
    TRANSLATE_CONTEXT_CONFIG = LLMConfig()
    TRANSLATE_CONTEXT_CONFIG.TEMPERATURE = 0.95
    TRANSLATE_CONTEXT_CONFIG.TOP_P = 0.95
    TRANSLATE_CONTEXT_CONFIG.MAX_TOKENS = 1024
    TRANSLATE_CONTEXT_CONFIG.FREQUENCY_PENALTY = 0

    # 类型映射表
    GROUP_MAPPING = {
        "角色" : ["姓氏", "名字"],
        "组织" : ["组织", "群体", "家族", "种族"],
        "地点" : ["地点", "建筑", "设施"],
        "物品" : ["物品", "食品", "工具"],
        "生物" : ["生物",],
    }
    GROUP_MAPPING_BANNED = {
        "黑名单" : ["行为", "活动", "其他", "无法判断"],
    }
    GROUP_MAPPING_ADDITIONAL = {
        "角色" : ["角色", "人", "人物", "人名"],
        "组织" : [],
        "地点" : [],
        "物品" : ["食物", "饮品",],
        "生物" : ["植物", "动物", "怪物", "魔物",],
    }

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

            # 如果响应数据有效，则是 llama.cpp 接口
            if isinstance(response_json, list) and len(response_json) > 0:
                self.request_frequency_threshold = len(response_json)
                LogHelper.info("")
                LogHelper.info(f"检查到 [green]llama.cpp[/]，根据其配置，请求频率阈值自动设置为 [green]{len(response_json)}[/] 次/秒 ...")
                LogHelper.info("")
            # 否则，按在线接口设置
            else:
                LLM.API_TEST_CONFIG.MAX_TOKENS = 4 * 1024
                LLM.SURFACE_ANALYSIS_CONFIG.MAX_TOKENS = 4 * 1024
                LLM.TRANSLATE_CONTEXT_CONFIG.MAX_TOKENS = 4 * 1024

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
                "temperature" : max(llm_config.TEMPERATURE, 0.50) if retry == True else llm_config.TEMPERATURE,
                "top_p" : llm_config.TOP_P,
                "max_tokens" : llm_config.MAX_TOKENS,
                # 同时设置 max_tokens 和 max_completion_tokens 时 OpenAI 接口会报错
                # "max_completion_tokens" : llm_config.MAX_TOKENS,
                "frequency_penalty" : max(llm_config.FREQUENCY_PENALTY, 0.2) if retry == True else llm_config.FREQUENCY_PENALTY,
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
                            "role": "user",
                            "content": (
                                self.prompt_surface_analysis_with_translation.replace("{PROMPT_GROUPS}", "、".join(("角色", "其他")))
                                + "\n" + "目标词语：ダリヤ"
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
                    raise Exception("未解析到有效数据 ...")

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
                if not hasattr(self, "prompt_groups"):
                    x = [v for group in LLM.GROUP_MAPPING.values() for v in group]
                    y = [v for group in LLM.GROUP_MAPPING_BANNED.values() for v in group]
                    self.prompt_groups = x + y

                if self.language != NER.Language.ZH:
                    prompt = self.prompt_surface_analysis_with_translation
                else:
                    prompt = self.prompt_surface_analysis_without_translation

                usage, message, llm_request, llm_response, error = await self.do_request(
                    [
                        {
                            "role": "user",
                            "content": (
                                prompt.replace("{PROMPT_GROUPS}", "、".join(self.prompt_groups))
                                + "\n" + f"目标词语：{word.surface}"
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
                    raise Exception("未解析到有效数据 ...")

                # 清理一下格式
                for k, v in result.items():
                    result[k] = re.sub(r".*[:：]+", "", TextHelper.strip_punctuation(v))

                # 获取结果
                word.group = result.get("group", "")
                word.gender = result.get("gender", "")
                word.context_summary = result.get("summary", "")
                word.surface_translation = result.get("translation", "")
                word.llmrequest_surface_analysis = llm_request
                word.llmresponse_surface_analysis = llm_response

                # 生成罗马音，汉字有时候会生成重复的罗马音，所以需要去重
                results = list(set([item.get("hepburn", "") for item in self.kakasi.convert(word.surface)]))
                word.surface_romaji = (" ".join(results)).strip()

                # 如果性别有效，则直接判断为角色类型
                if word.gender in ("男", "女"):
                    word.group = "角色"
                    LogHelper.debug(f"[词义分析] 性别有效 - {word.surface} [green]->[/] {word.group} ...")
                else:
                    # 匹配实体类型
                    matched = False
                    for k, v in LLM.GROUP_MAPPING.items():
                        if word.group in set(v):
                            word.group = k
                            matched = True
                            break
                    for k, v in LLM.GROUP_MAPPING_ADDITIONAL.items():
                        if word.group in set(v):
                            LogHelper.debug(f"[词义分析] 命中额外类型 - {word.surface} [green]->[/] {word.group} ...")
                            word.group = k
                            matched = True
                            break
                    if matched == False:
                        LogHelper.warning(f"[词义分析] 无法匹配的实体类型 - {word.surface} [green]->[/] {word.group} ...")
                        word.group = ""
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

        for i in range(LLM.MAX_RETRY + 1):
            if i == 0:
                retry = False
                words_this_round = words
            elif len(failure) > 0:
                retry = True
                words_this_round = failure
                LogHelper.warning(f"[词义分析] 即将开始第 {i} / {LLM.MAX_RETRY} 轮重试...")
            else:
                break

            # 执行异步任务
            tasks = [
                asyncio.create_task(self.surface_analysis(word, words, success, retry))
                for word in words_this_round
            ]
            await asyncio.gather(*tasks, return_exceptions = True)

            # 获得失败任务的列表
            success_pairs = {(word.surface, word.group) for word in success}
            failure = [word for word in words if (word.surface, word.group) not in success_pairs]

        return words

    # 参考文本翻译任务
    async def context_translate(self, word: Word, words: list[Word], success: list[Word], retry: bool) -> None:
        async with self.semaphore, self.async_limiter:
            try:
                usage, message, llm_request, llm_response, error = await self.do_request(
                    [
                        {
                            "role": "user",
                            "content": (
                                self.prompt_context_translate
                                + "\n" + f"轻小说文本：\n{word.get_context_str_for_translate(self.language)}"
                            ),
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
                LogHelper.warning(f"[参考文本翻译] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")
                LogHelper.debug(f"llm_request - {llm_request}")
                LogHelper.debug(f"llm_response - {llm_response}")
                error = e
            finally:
                if error == None:
                    with self.lock:
                        success.append(word)
                    LogHelper.info(f"[参考文本翻译] 已完成 {len(success)} / {len(words)} ...")

    # 批量执行参考文本翻译任务
    async def context_translate_batch(self, words: list[Word]) -> list[Word]:
        failure = []
        success = []

        for i in range(LLM.MAX_RETRY + 1):
            if i == 0:
                retry = False
                words_this_round = words
            elif len(failure) > 0:
                retry = True
                words_this_round = failure
                LogHelper.warning(f"[参考文本翻译] 即将开始第 {i} / {LLM.MAX_RETRY} 轮重试...")
            else:
                break

            # 执行异步任务
            tasks = [
                asyncio.create_task(self.context_translate(word, words, success, retry))
                for word in words_this_round
            ]
            await asyncio.gather(*tasks, return_exceptions = True)

            # 获得失败任务的列表
            success_pairs = {(word.surface, word.group) for word in success}
            failure = [word for word in words if (word.surface, word.group) not in success_pairs]

        return words