import os
import json
import itertools

from base.Base import Base
from module.Cache.CacheItem import CacheItem
from module.File.TRANS.KAG import KAG
from module.File.TRANS.NONE import NONE
from module.File.TRANS.WOLF import WOLF
from module.File.TRANS.RENPY import RENPY
from module.File.TRANS.RPGMAKER import RPGMAKER

class TRANS(Base):

    def __init__(self, config: dict) -> None:
        super().__init__()

        # 初始化
        self.config: dict = config
        self.input_path: str = config.get("input_folder")
        self.output_path: str = config.get("output_folder")
        self.source_language: str = config.get("source_language")
        self.target_language: str = config.get("target_language")

    # 读取
    def read_from_path(self, abs_paths: list[str]) -> list[CacheItem]:
        items: list[CacheItem] = []
        for abs_path in abs_paths:
            # 获取相对路径
            rel_path = os.path.relpath(abs_path, self.input_path)

            # 数据处理
            with open(abs_path, "r", encoding = "utf-8-sig") as reader:
                json_data = json.load(reader)

                # 有效性校验
                if not isinstance(json_data, dict):
                    continue

                # 获取项目信息
                project: dict = json_data.get("project", {})

                # 获取处理实体
                processor: NONE = self.get_processor(project)
                processor.pre_process()

                # 处理数据
                path: str = ""
                entry: dict = {}
                files: dict = project.get("files", {})
                for path, entry in files.items():
                    for tag, data, context, parameter in itertools.zip_longest(
                        entry.get("tags", []),
                        entry.get("data", []),
                        entry.get("context", []),
                        entry.get("parameters", []),
                        fillvalue = None
                    ):
                        # 处理可能为 None 的情况
                        tag: list[str] = tag if tag is not None else []
                        data: list[str] = data if data is not None else []
                        context: list[str] = context if context is not None else []
                        parameter: list[str] = parameter if parameter is not None else []

                        # 检查并添加数据
                        src, dst, tag, status, skip_internal_filter = processor.check(path, data, tag, context)
                        items.append(
                            CacheItem({
                                "src": src,
                                "dst": dst,
                                "extra_field": {
                                    "tag": tag,
                                    "context": context,
                                    "parameter": parameter,
                                },
                                "tag": path,
                                "row": len(items),
                                "file_type": CacheItem.FileType.TRANS,
                                "file_path": rel_path,
                                "text_type": processor.TEXT_TYPE,
                                "status": status,
                                "skip_internal_filter": skip_internal_filter,
                            })
                        )

            # 去重
            translation: dict[str, str] = {}
            for item in [v for v in items if v.get_status() == Base.TranslationStatus.UNTRANSLATED]:
                src = item.get_src()
                dst = item.get_dst()
                if src not in translation:
                    translation[src] = dst
                else:
                    item.set_status(Base.TranslationStatus.DUPLICATED)

        return items

    # 获取处理实体
    def get_processor(self, project: dict) -> NONE:
        engine: str = project.get("gameEngine", "")

        if engine.lower() in ("kag", "vntrans"):
            processor: NONE = KAG(project)
        elif engine.lower() in ("wolf", "wolfrpg"):
            processor: NONE = WOLF(project)
        elif engine.lower() in ("renpy", ):
            processor: NONE = RENPY(project)
        elif engine.lower() in ("2k", "rmjdb", "rmvx", "rmvxace", "rmmv", "rmmz"):
            processor: NONE = RPGMAKER(project)
        else:
            processor: NONE = NONE(project)

        return processor