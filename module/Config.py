import dataclasses
import json
import os
import threading
from enum import StrEnum
from typing import Any
from typing import ClassVar
from typing import Self

from base.BaseLanguage import BaseLanguage
from base.LogManager import LogManager
from module.Localizer.Localizer import Localizer

@dataclasses.dataclass
class Config():

    class Theme(StrEnum):

        DARK = "DARK"
        LIGHT = "LIGHT"

    # Application
    theme: str = Theme.LIGHT
    app_language: BaseLanguage.Enum = BaseLanguage.Enum.ZH

    # PlatformPage
    activate_platform: int = 0
    platforms: list[dict[str, Any]] = None

    # AppSettingsPage
    expert_mode: bool = True
    proxy_url: str = ""
    proxy_enable: bool = False
    font_hinting: bool = True
    scale_factor: str = ""

    # BasicSettingsPage
    token_threshold: int = 2048
    max_workers: int = 0
    rpm_threshold: int = 0
    request_timeout: int = 120
    max_round: int = 16

    # ProjectPage
    source_language: BaseLanguage.Enum = BaseLanguage.Enum.JA
    target_language: BaseLanguage.Enum = BaseLanguage.Enum.ZH
    input_folder: str = "./input"
    output_folder: str = "./output"
    output_folder_open_on_finish: bool = False
    traditional_chinese_enable: bool = False

    # CustomPromptZHPage
    custom_prompt_zh_enable: bool = False
    custom_prompt_zh_data: str = None

    # CustomPromptENPage
    custom_prompt_en_enable: bool = False
    custom_prompt_en_data: str = None

    # 类属性
    CONFIG_PATH: ClassVar[str] = "./resource/config.json"
    CONFIG_LOCK: ClassVar[threading.Lock] = threading.Lock()

    def load(self, path: str = None) -> Self:
        if path is None:
            path = __class__.CONFIG_PATH

        with __class__.CONFIG_LOCK:
            try:
                os.makedirs(os.path.dirname(path), exist_ok = True)
                if os.path.isfile(path):
                    with open(path, "r", encoding = "utf-8-sig") as reader:
                        config: dict = json.load(reader)
                        for k, v in config.items():
                            if hasattr(self, k):
                                setattr(self, k, v)
            except Exception as e:
                LogManager.get().error(f"{Localizer.get().log_read_file_fail}", e)

        return self

    def save(self, path: str = None) -> Self:
        if path is None:
            path = __class__.CONFIG_PATH

        with __class__.CONFIG_LOCK:
            try:
                os.makedirs(os.path.dirname(path), exist_ok = True)
                with open(path, "w", encoding = "utf-8") as writer:
                    json.dump(dataclasses.asdict(self), writer, indent = 4, ensure_ascii = False)
            except Exception as e:
                LogManager.get().error(f"{Localizer.get().log_write_file_fail}", e)

        return self

    # 重置专家模式
    def reset_expert_settings(self) -> None:
        pass

    # 获取平台配置
    def get_platform(self, id: int) -> dict[str, Any]:
        item: dict[str, str | bool | int | float | list[str]] = None
        for item in self.platforms:
            if item.get("id", 0) == id:
                return item

    # 更新平台配置
    def set_platform(self, platform: dict[str, Any]) -> None:
        for i, item in enumerate(self.platforms):
            if item.get("id", 0) == platform.get("id", 0):
                self.platforms[i] = platform
                break