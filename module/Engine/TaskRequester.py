import json
import re
import threading
from functools import lru_cache

import anthropic
import httpx
import openai
from google import genai
from google.genai import types

from base.Base import Base
from base.VersionManager import VersionManager
from module.Config import Config
from module.Localizer.Localizer import Localizer

class TaskRequester(Base):

    # 密钥索引
    API_KEY_INDEX: int = 0

    # qwen3_instruct_8b_q6k
    RE_QWEN3: re.Pattern = re.compile(r"qwen3", flags = re.IGNORECASE)

    # gemini-2.5-flash
    RE_GEMINI_2_5_FLASH: re.Pattern = re.compile(r"gemini-2\.5-flash", flags = re.IGNORECASE)

    # Claude
    RE_CLAUDE: tuple[re.Pattern] = (
        re.compile(r"claude-3-7-sonnet", flags = re.IGNORECASE),
        re.compile(r"claude-opus-4-0", flags = re.IGNORECASE),
        re.compile(r"claude-sonnet-4-0", flags = re.IGNORECASE),
    )

    # o1 o3-mini o4-mini-20240406
    RE_O_SERIES: re.Pattern = re.compile(r"o\d$|o\d-", flags = re.IGNORECASE)

    # 正则
    RE_LINE_BREAK: re.Pattern = re.compile(r"\n+")

    # 类线程锁
    LOCK: threading.Lock = threading.Lock()

    def __init__(self, config: Config, platform: dict[str, str | bool | int | float | list]) -> None:
        super().__init__()

        # 初始化
        self.config = config
        self.platform = platform

    # 重置
    @classmethod
    def reset(cls) -> None:
        cls.API_KEY_INDEX: int = 0
        cls.get_client.cache_clear()

    @classmethod
    def get_key(cls, keys: list[str]) -> str:
        key: str = ""

        if len(keys) == 0:
            key = "no_key_required"
        elif len(keys) == 1:
            key = keys[0]
        elif cls.API_KEY_INDEX >= len(keys) - 1:
            key = keys[0]
            cls.API_KEY_INDEX = 0
        else:
            key = keys[cls.API_KEY_INDEX]
            cls.API_KEY_INDEX = cls.API_KEY_INDEX + 1

        return key

    # 获取客户端
    @classmethod
    @lru_cache(maxsize = None)
    def get_client(cls, url: str, key: str, format: Base.APIFormat, timeout: int) -> openai.OpenAI | genai.Client | anthropic.Anthropic:
        # connect (连接超时):
        #   建议值: 5.0 到 10.0 秒。
        #   解释: 建立到 LLM API 服务器的 TCP 连接。通常这个过程很快，但网络波动时可能需要更长时间。设置过短可能导致在网络轻微抖动时连接失败。
        # read (读取超时):
        #   建议值: 非常依赖具体场景。
        #   对于快速响应的简单任务（如分类、简单问答）：10.0 到 30.0 秒。
        #   对于中等复杂任务或中等长度输出：30.0 到 90.0 秒。
        #   对于复杂任务或长文本生成（如 GPT-4 生成大段代码或文章）：60.0 到 180.0 秒，甚至更长。
        #   解释: 这是从发送完请求到接收完整个响应体的最大时间。这是 LLM 请求中最容易超时的部分。你需要根据你的模型、提示和期望输出来估算一个合理的上限。强烈建议监控你的P95/P99响应时间来调整这个值。
        # write (写入超时):
        #   建议值: 5.0 到 10.0 秒。
        #   解释: 发送请求体（包含你的 prompt）到服务器的时间。除非你的 prompt 非常巨大（例如，包含超长上下文），否则这个过程通常很快。
        # pool (从连接池获取连接超时):
        #   建议值: 5.0 到 10.0 秒 (如果并发量高，可以适当增加)。
        #   解释: 如果你使用 httpx.Client 并且并发发起大量请求，可能会耗尽连接池中的连接。此参数定义了等待可用连接的最长时间。
        if format == Base.APIFormat.SAKURALLM:
            return openai.OpenAI(
                base_url = url,
                api_key = key,
                timeout = httpx.Timeout(
                    read = timeout,
                    pool = 8.00,
                    write = 8.00,
                    connect = 8.00,
                ),
                max_retries = 1,
            )
        elif format == Base.APIFormat.GOOGLE:
            # https://github.com/googleapis/python-genai
            return genai.Client(
                api_key = key,
                http_options = types.HttpOptions(
                    base_url = url,
                    timeout = timeout * 1000,
                    headers = {
                        "User-Agent": f"KeywordGacha/{VersionManager.get().get_version()} (https://github.com/neavo/KeywordGacha)",
                    },
                ),
            )
        elif format == Base.APIFormat.ANTHROPIC:
            return anthropic.Anthropic(
                base_url = url,
                api_key = key,
                timeout = httpx.Timeout(
                    read = timeout,
                    pool = 8.00,
                    write = 8.00,
                    connect = 8.00,
                ),
                max_retries = 1,
            )
        else:
            return openai.OpenAI(
                base_url = url,
                api_key = key,
                timeout = httpx.Timeout(
                    read = timeout,
                    pool = 8.00,
                    write = 8.00,
                    connect = 8.00,
                ),
                max_retries = 1,
            )

    # 发起请求
    def request(self, messages: list[dict]) -> tuple[bool, str, int, int]:
        args: dict[str, float] = {}
        if self.platform.get("top_p_custom_enable") == True:
            args["top_p"] = self.platform.get("top_p")
        if self.platform.get("temperature_custom_enable") == True:
            args["temperature"] = self.platform.get("temperature")
        if self.platform.get("presence_penalty_custom_enable") == True:
            args["presence_penalty"] = self.platform.get("presence_penalty")
        if self.platform.get("frequency_penalty_custom_enable") == True:
            args["frequency_penalty"] = self.platform.get("frequency_penalty")

        thinking = self.platform.get("thinking")

        # 发起请求
        if self.platform.get("api_format") == Base.APIFormat.SAKURALLM:
            skip, response_think, response_result, input_tokens, output_tokens = self.request_sakura(
                messages,
                thinking,
                args,
            )
        elif self.platform.get("api_format") == Base.APIFormat.GOOGLE:
            skip, response_think, response_result, input_tokens, output_tokens = self.request_google(
                messages,
                thinking,
                args,
            )
        elif self.platform.get("api_format") == Base.APIFormat.ANTHROPIC:
            skip, response_think, response_result, input_tokens, output_tokens = self.request_anthropic(
                messages,
                thinking,
                args,
            )
        else:
            skip, response_think, response_result, input_tokens, output_tokens = self.request_openai(
                messages,
                thinking,
                args,
            )

        return skip, response_think, response_result, input_tokens, output_tokens

    # 生成请求参数
    def generate_sakura_args(self, messages: list[dict[str, str]], thinking: bool, args: dict[str, float]) -> dict:
        args: dict = args | {
            "model": self.platform.get("model"),
            "messages": messages,
            "max_tokens": max(512, self.config.token_threshold),
            "extra_headers": {
                "User-Agent": f"KeywordGacha/{VersionManager.get().get_version()} (https://github.com/neavo/KeywordGacha)"
            }
        }

        return args

    # 发起请求
    def request_sakura(self, messages: list[dict[str, str]], thinking: bool, args: dict[str, float]) -> tuple[bool, str, str, int, int]:
        try:
            # 获取客户端
            with __class__.LOCK:
                client: openai.OpenAI = __class__.get_client(
                    url = self.platform.get("api_url"),
                    key = __class__.get_key(self.platform.get("api_key")),
                    format = self.platform.get("api_format"),
                    timeout = self.config.request_timeout,
                )

            # 发起请求
            response: openai.types.completion.Completion = client.chat.completions.create(
                **self.generate_sakura_args(messages, thinking, args)
            )

            # 提取回复的文本内容
            response_result = response.choices[0].message.content
        except Exception as e:
            self.error(f"{Localizer.get().log_task_fail}", e)
            return True, None, None, None, None

        # 获取输入消耗
        try:
            input_tokens = int(response.usage.prompt_tokens)
        except Exception:
            input_tokens = 0

        # 获取输出消耗
        try:
            output_tokens = int(response.usage.completion_tokens)
        except Exception:
            output_tokens = 0

        # Sakura 返回的内容多行文本，将其转换为 JSON 字符串
        response_result = json.dumps(
            {str(i): line.strip() for i, line in enumerate(response_result.strip().splitlines())},
            indent = None,
            ensure_ascii = False,
        )

        return False, "", response_result, input_tokens, output_tokens

    # 生成请求参数
    def generate_openai_args(self, messages: list[dict[str, str]], thinking: bool, args: dict[str, float]) -> dict:
        args: dict = args | {
            "model": self.platform.get("model"),
            "messages": messages,
            "max_tokens": max(4 * 1024, self.config.token_threshold),
            "extra_headers": {
                "User-Agent": f"KeywordGacha/{VersionManager.get().get_version()} (https://github.com/neavo/KeywordGacha)"
            }
        }

        # OpenAI O-Series 模型兼容性处理
        if (
            self.platform.get("api_url").startswith("https://api.openai.com") or
            __class__.RE_O_SERIES.search(self.platform.get("model")) is not None
        ):
            args.pop("max_tokens", None)
            args["max_completion_tokens"] = max(4 * 1024, self.config.token_threshold)

        # 思考模式切换 - QWEN3
        if __class__.RE_QWEN3.search(self.platform.get("model")) is not None:
            if thinking == True:
                pass
            else:
                if "/no_think" not in messages[-1].get("content", ""):
                    messages[-1]["content"] = messages[-1].get("content") + "\n" + "/no_think"

        return args

    # 发起请求
    def request_openai(self, messages: list[dict[str, str]], thinking: bool, args: dict[str, float]) -> tuple[bool, str, str, int, int]:
        try:
            # 获取客户端
            with __class__.LOCK:
                client: openai.OpenAI = __class__.get_client(
                    url = self.platform.get("api_url"),
                    key = __class__.get_key(self.platform.get("api_key")),
                    format = self.platform.get("api_format"),
                    timeout = self.config.request_timeout,
                )

            # 发起请求
            response: openai.types.completion.Completion = client.chat.completions.create(
                **self.generate_openai_args(messages, thinking, args)
            )

            # 提取回复内容
            message = response.choices[0].message
            if hasattr(message, "reasoning_content") and isinstance(message.reasoning_content, str):
                response_think = __class__.RE_LINE_BREAK.sub("\n", message.reasoning_content.strip())
                response_result = message.content.strip()
            elif "</think>" in message.content:
                splited = message.content.split("</think>")
                response_think = __class__.RE_LINE_BREAK.sub("\n", splited[0].removeprefix("<think>").strip())
                response_result = splited[-1].strip()
            else:
                response_think = ""
                response_result = message.content.strip()
        except Exception as e:
            self.error(f"{Localizer.get().log_task_fail}", e)
            return True, None, None, None, None

        # 获取输入消耗
        try:
            input_tokens = int(response.usage.prompt_tokens)
        except Exception:
            input_tokens = 0

        # 获取输出消耗
        try:
            output_tokens = int(response.usage.completion_tokens)
        except Exception:
            output_tokens = 0

        return False, response_think, response_result, input_tokens, output_tokens

    # 生成请求参数
    def generate_google_args(self, messages: list[dict[str, str]], thinking: bool, args: dict[str, float]) -> dict[str, str | int | float]:
        args: dict = args | {
            "max_output_tokens": max(4 * 1024, self.config.token_threshold),
            "safety_settings": (
                types.SafetySetting(
                    category = "HARM_CATEGORY_HARASSMENT",
                    threshold = "BLOCK_NONE",
                ),
                types.SafetySetting(
                    category = "HARM_CATEGORY_HATE_SPEECH",
                    threshold = "BLOCK_NONE",
                ),
                types.SafetySetting(
                    category = "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold = "BLOCK_NONE",
                ),
                types.SafetySetting(
                    category = "HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold = "BLOCK_NONE",
                ),
            ),
        }

        # 思考模式切换 - Gemini 2.5 Flash
        if __class__.RE_GEMINI_2_5_FLASH.search(self.platform.get("model")) is not None:
            if thinking == True:
                args["thinking_config"] = types.ThinkingConfig(
                    thinking_budget = 1024,
                    include_thoughts = True,
                )
            else:
                args["thinking_config"] = types.ThinkingConfig(
                    thinking_budget = 0,
                    include_thoughts = False,
                )

        return {
            "model": self.platform.get("model"),
            "contents": [v.get("content") for v in messages if v.get("role") == "user"],
            "config": types.GenerateContentConfig(**args),
        }

    # 发起请求
    def request_google(self, messages: list[dict[str, str]], thinking: bool, args: dict[str, float]) -> tuple[bool, str, int, int]:
        try:
            # 获取客户端
            with __class__.LOCK:
                client: genai.Client = __class__.get_client(
                    url = self.platform.get("api_url"),
                    key = __class__.get_key(self.platform.get("api_key")),
                    format = self.platform.get("api_format"),
                    timeout = self.config.request_timeout,
                )

            # 发起请求
            response: types.GenerateContentResponse = client.models.generate_content(
                **self.generate_google_args(messages, thinking, args)
            )

            # 提取回复内容
            response_think = ""
            response_result = ""
            if len(response.candidates) > 0 and len(response.candidates[-1].content.parts) > 0:
                parts = response.candidates[-1].content.parts
                think_messages = [v for v in parts if v.thought == True]
                if len(think_messages) > 0:
                    response_think = __class__.RE_LINE_BREAK.sub("\n", think_messages[-1].text.strip())
                result_messages = [v for v in parts if v.thought != True]
                if len(result_messages) > 0:
                    response_result = result_messages[-1].text.strip()
        except Exception as e:
            self.error(f"{Localizer.get().log_task_fail}", e)
            return True, None, None, None, None

        # 获取输入消耗
        try:
            input_tokens = int(response.usage_metadata.prompt_token_count)
        except Exception:
            input_tokens = 0

        # 获取输出消耗
        try:
            total_token_count = int(response.usage_metadata.total_token_count)
            prompt_token_count = int(response.usage_metadata.prompt_token_count)
            output_tokens = total_token_count - prompt_token_count
        except Exception:
            output_tokens = 0

        return False, response_think, response_result, input_tokens, output_tokens

    # 生成请求参数
    def generate_anthropic_args(self, messages: list[dict[str, str]], thinking: bool, args: dict[str, float]) -> dict:
        args: dict = args | {
            "model": self.platform.get("model"),
            "messages": messages,
            "max_tokens": max(4 * 1024, self.config.token_threshold),
            "extra_headers": {
                "User-Agent": f"KeywordGacha/{VersionManager.get().get_version()} (https://github.com/neavo/KeywordGacha)"
            }
        }

        # 移除 Anthropic 模型不支持的参数
        args.pop("presence_penalty", None)
        args.pop("frequency_penalty", None)

        # 思考模式切换
        if any(v.search(self.platform.get("model")) is not None for v in __class__.RE_CLAUDE):
            if thinking == True:
                args["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": 1024,
                }
            else:
                pass

        return args

    # 发起请求
    def request_anthropic(self, messages: list[dict[str, str]], thinking: bool, args: dict[str, float]) -> tuple[bool, str, str, int, int]:
        try:
            # 获取客户端
            with __class__.LOCK:
                client: anthropic.Anthropic = __class__.get_client(
                    url = self.platform.get("api_url"),
                    key = __class__.get_key(self.platform.get("api_key")),
                    format = self.platform.get("api_format"),
                    timeout = self.config.request_timeout,
                )

            # 发起请求
            response: anthropic.types.Message = client.messages.create(
                **self.generate_anthropic_args(messages, thinking, args)
            )

            # 提取回复内容
            text_messages = [msg for msg in response.content if hasattr(msg, "text") and isinstance(msg.text, str)]
            think_messages = [msg for msg in response.content if hasattr(msg, "thinking") and isinstance(msg.thinking, str)]

            if text_messages != []:
                response_result = text_messages[-1].text.strip()
            else:
                response_result = ""

            if think_messages != []:
                response_think = __class__.RE_LINE_BREAK.sub("\n", think_messages[-1].thinking.strip())
            else:
                response_think = ""
        except Exception as e:
            self.error(f"{Localizer.get().log_task_fail}", e)
            return True, None, None, None, None

        # 获取输入消耗
        try:
            input_tokens = int(response.usage.input_tokens)
        except Exception:
            input_tokens = 0

        # 获取输出消耗
        try:
            output_tokens = int(response.usage.output_tokens)
        except Exception:
            output_tokens = 0

        return False, response_think, response_result, input_tokens, output_tokens