import threading
from functools import lru_cache

from base.Base import Base
from base.BaseLanguage import BaseLanguage
from module.Config import Config

class PromptBuilder(Base):

    # 类线程锁
    LOCK: threading.Lock = threading.Lock()

    def __init__(self, config: Config) -> None:
        super().__init__()

        # 初始化
        self.config: Config = config

    @classmethod
    def reset(cls) -> None:
        cls.get_base.cache_clear()
        cls.get_prefix.cache_clear()
        cls.get_suffix.cache_clear()

    @classmethod
    @lru_cache(maxsize = None)
    def get_base(cls, language: BaseLanguage.Enum) -> str:
        with open(f"resource/prompt/{language.lower()}/base.txt", "r", encoding = "utf-8-sig") as reader:
            return reader.read().strip()

    @classmethod
    @lru_cache(maxsize = None)
    def get_prefix(cls, language: BaseLanguage.Enum) -> str:
        with open(f"resource/prompt/{language.lower()}/prefix.txt", "r", encoding = "utf-8-sig") as reader:
            return reader.read().strip()

    @classmethod
    @lru_cache(maxsize = None)
    def get_suffix(cls, language: BaseLanguage.Enum) -> str:
        with open(f"resource/prompt/{language.lower()}/suffix.txt", "r", encoding = "utf-8-sig") as reader:
            return reader.read().strip()

    # 获取主提示词
    def build_main(self) -> str:
        # 判断提示词语言
        if self.config.target_language == BaseLanguage.Enum.ZH:
            prompt_language = BaseLanguage.Enum.ZH
            source_language = BaseLanguage.get_name_zh(self.config.source_language)
            target_language = BaseLanguage.get_name_zh(self.config.target_language)
        else:
            prompt_language = BaseLanguage.Enum.EN
            source_language = BaseLanguage.get_name_en(self.config.source_language)
            target_language = BaseLanguage.get_name_en(self.config.target_language)

        with __class__.LOCK:
            # 前缀
            prefix = __class__.get_prefix(prompt_language)

            # 基本
            if prompt_language == BaseLanguage.Enum.ZH and self.config.custom_prompt_zh_enable == True:
                base = self.config.custom_prompt_zh_data
            elif prompt_language == BaseLanguage.Enum.EN and self.config.custom_prompt_en_enable == True:
                base = self.config.custom_prompt_en_data
            else:
                base = __class__.get_base(prompt_language)

            # 后缀
            suffix = __class__.get_suffix(prompt_language)

        # 组装提示词
        full_prompt = prefix + "\n" + base + "\n" + suffix
        full_prompt = full_prompt.replace("{source_language}", source_language)
        full_prompt = full_prompt.replace("{target_language}", target_language)

        return full_prompt

    # 构建输入
    def build_inputs(self, srcs: list[str]) -> str:
        if self.config.target_language == BaseLanguage.Enum.ZH:
            return (
                "文本片段："
                "\n" + "\n".join(srcs)
            )
        else:
            return (
                "Text Snippet:"
                "\n" + "\n".join(srcs)
            )

    # 生成提示词
    def generate_prompt(self, srcs: list[str]) -> tuple[list[dict], list[str]]:
        # 初始化
        messages: list[dict[str, str]] = []
        console_log: list[str] = []

        # 基础提示词
        content = self.build_main()

        # 输入
        result = self.build_inputs(srcs)
        if result != "":
            content = content + "\n" + result

        # 构建提示词列表
        messages.append({
            "role": "user",
            "content": content,
        })

        return messages, console_log