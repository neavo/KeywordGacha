import re
import threading

import tiktoken
import tiktoken_ext
from tiktoken_ext import openai_public

from base.Base import Base
from base.BaseData import BaseData
from module.Text.TextBase import TextBase

class CacheItem(BaseData):

    # 必须显式的引用这两个库，否则打包后会报错
    tiktoken_ext
    openai_public

    class FileType():

        MD: str = "MD"                                  # .md Markdown
        TXT: str = "TXT"                                # .txt 文本文件
        SRT: str = "SRT"                                # .srt 字幕文件
        ASS: str = "ASS"                                # .ass 字幕文件
        EPUB: str = "EPUB"                              # .epub
        XLSX: str = "XLSX"                              # .xlsx Translator++ SExtractor
        WOLFXLSX: str = "WOLFXLSX"                      # .xlsx WOLF 官方翻译工具导出文件
        RENPY: str = "RENPY"                            # .rpy RenPy
        TRANS: str = "TRANS"                            # .trans Translator++
        KVJSON: str = "KVJSON"                          # .json MTool
        MESSAGEJSON: str = "MESSAGEJSON"                # .json SExtractor

    class TextType():

        NONE: str = "NONE"                              # 无类型，即纯文本
        MD: str = "MD"                                  # Markdown
        KAG: str = "KAG"                                # KAG 游戏文本
        WOLF: str = "WOLF"                              # WOLF 游戏文本
        RENPY: str = "RENPY"                            # RENPY 游戏文本
        RPGMAKER: str = "RPGMAKER"                      # RPGMAKER 游戏文本

    # 缓存 Token 数量
    TOKEN_COUNT_CACHE: dict[str, int] = {}

    # WOLF
    REGEX_WOLF: tuple[re.Pattern] = (
        re.compile(r"@\d+", flags = re.IGNORECASE),                                             # 角色 ID
        re.compile(r"\\[cus]db\[.+?:.+?:.+?\]", flags = re.IGNORECASE),                         # 数据库变量 \cdb[0:1:2]
    )

    # RENPY
    CJK_RANGE: str = rf"{TextBase.CJK_RANGE}{TextBase.HANGUL_RANGE}{TextBase.HIRAGANA_RANGE}{TextBase.KATAKANA_RANGE}"
    REGEX_RENPY: tuple[re.Pattern] = (
        re.compile(r"\{[^\{" + CJK_RANGE + r"]*?\}", flags = re.IGNORECASE),                    # {w=2.3}
        re.compile(r"\[[^\[" + CJK_RANGE + r"]*?\]", flags = re.IGNORECASE),                    # [renpy.version_only]
    )

    # RPGMaker
    REGEX_RPGMaker: tuple[re.Pattern] = (
        re.compile(r"en\(.{0,8}[vs]\[\d+\].{0,16}\)", flags = re.IGNORECASE),                    # en(!s[982]) en(v[982] >= 1)
        re.compile(r"if\(.{0,8}[vs]\[\d+\].{0,16}\)", flags = re.IGNORECASE),                    # if(!s[982]) if(v[982] >= 1)
        re.compile(r"[/\\][a-z]{1,8}[<\[][a-z\d]{0,16}[>\]]", flags = re.IGNORECASE),            # /c[xy12] \bc[xy12] <\bc[xy12]>
    )

    def __init__(self, args: dict) -> None:
        super().__init__()

        # 默认值
        self.src: str = ""                                              # 原文
        self.dst: str = ""                                              # 译文
        self.name_src: str | tuple[str] = None                          # 角色姓名原文
        self.name_dst: str | tuple[str] = None                          # 角色姓名译文
        self.extra_field: str | dict = ""                               # 额外字段原文
        self.tag: str = ""                                              # 标签
        self.row: int = 0                                               # 行号
        self.file_type: str = ""                                        # 原始文件的类型
        self.file_path: str = ""                                        # 原始文件的相对路径
        self.text_type: str = CacheItem.TextType.NONE                   # 文本的实际类型
        self.status: str = Base.TranslationStatus.UNTRANSLATED          # 翻译状态
        self.retry_count: int = 0                                       # 重试次数，当前只有单独重试的时候才增加此计数
        self.skip_internal_filter: bool = False                         # 跳过内置过滤器

        # 初始化
        for k, v in args.items():
            setattr(self, k, v)

        # 线程锁
        self.lock = threading.Lock()

        # 如果文件类型是 XLSX、TRANS、KVJSON、MESSAGEJSON，且没有文本类型，则判断实际的文本类型
        if (
            self.get_file_type() in (CacheItem.FileType.XLSX, CacheItem.FileType.KVJSON, CacheItem.FileType.MESSAGEJSON)
            and self.get_text_type() == CacheItem.TextType.NONE
        ):
            if any(v.search(self.get_src()) is not None for v in CacheItem.REGEX_WOLF):
                self.set_text_type(CacheItem.TextType.WOLF)
            elif any(v.search(self.get_src()) is not None for v in CacheItem.REGEX_RPGMaker):
                self.set_text_type(CacheItem.TextType.RPGMAKER)
            elif any(v.search(self.get_src()) is not None for v in CacheItem.REGEX_RENPY):
                self.set_text_type(CacheItem.TextType.RENPY)

    # 获取原文
    def get_src(self) -> str:
        with self.lock:
            return self.src

    # 设置原文
    def set_src(self, src: str) -> None:
        with self.lock:
            self.src = src

    # 获取译文
    def get_dst(self) -> str:
        with self.lock:
            return self.dst

    # 设置译文
    def set_dst(self, dst: str) -> None:
        with self.lock:
            # 有时候模型的回复反序列化以后会是 int 等非字符类型，所以这里要强制转换成字符串
            # TODO:可能需要更好的处理方式
            if isinstance(dst, str):
                self.dst = dst
            else:
                self.dst = str(dst)

    # 获取角色姓名原文
    def get_name_src(self) -> str | tuple[str]:
        with self.lock:
            return self.name_src

    # 设置角色姓名原文
    def set_name_src(self, name_src: str | tuple[str]) -> None:
        with self.lock:
            self.name_src = name_src

    # 获取角色姓名译文
    def get_name_dst(self) -> str | tuple[str]:
        with self.lock:
            return self.name_dst

    # 设置角色姓名译文
    def set_name_dst(self, name_dst: str | tuple[str]) -> None:
        with self.lock:
            self.name_dst = name_dst

    # 获取额外字段原文
    def get_extra_field(self) -> str | dict:
        with self.lock:
            return self.extra_field

    # 设置额外字段原文
    def set_extra_field(self, extra_field: str | dict) -> None:
        with self.lock:
            self.extra_field = extra_field

    # 获取标签
    def get_tag(self) -> str:
        with self.lock:
            return self.tag

    # 设置标签
    def set_tag(self, tag: str) -> None:
        with self.lock:
            self.tag = tag

    # 获取行号
    def get_row(self) -> int:
        with self.lock:
            return self.row

    # 设置行号
    def set_row(self, row: int) -> None:
        with self.lock:
            self.row = row

    # 获取文件类型
    def get_file_type(self) -> str:
        with self.lock:
            return self.file_type

    # 设置文件类型
    def set_file_type(self, type: str) -> None:
        with self.lock:
            self.file_type = type

    # 获取文件路径
    def get_file_path(self) -> str:
        with self.lock:
            return self.file_path

    # 设置文件路径
    def set_file_path(self, path: str) -> None:
        with self.lock:
            self.file_path = path

    # 获取文本类型
    def get_text_type(self) -> str:
        with self.lock:
            return self.text_type

    # 设置文本类型
    def set_text_type(self, type: str) -> None:
        with self.lock:
            self.text_type = type

    # 获取翻译状态
    def get_status(self) -> str:
        with self.lock:
            return self.status

    # 设置翻译状态
    def set_status(self, status: str) -> None:
        with self.lock:
            self.status = status

    # 获取重试次数
    def get_retry_count(self) -> int:
        with self.lock:
            return self.retry_count

    # 设置重试次数
    def set_retry_count(self, retry_count: int) -> None:
        with self.lock:
            self.retry_count = retry_count

    # 获取跳过内置过滤器
    def get_skip_internal_filter(self) -> bool:
        with self.lock:
            return self.skip_internal_filter

    # 设置跳过内置过滤器
    def set_skip_internal_filter(self, skip_internal_filter: bool) -> None:
        with self.lock:
            self.skip_internal_filter = skip_internal_filter

    # 获取 Token 数量
    def get_token_count(self) -> int:
        with self.lock:
            if self.src not in CacheItem.TOKEN_COUNT_CACHE:
                CacheItem.TOKEN_COUNT_CACHE[self.src] = len(tiktoken.get_encoding("o200k_base").encode(self.src))

            return CacheItem.TOKEN_COUNT_CACHE[self.src]