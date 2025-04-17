import os

import rapidjson as json

from base.Base import Base
from module.Cache.CacheItem import CacheItem

class KVJSON(Base):

    # {
    #     "「あ・・」": "「あ・・」",
    #     "「ごめん、ここ使う？」": "「ごめん、ここ使う？」",
    #     "「じゃあ・・私は帰るね」": "「じゃあ・・私は帰るね」",
    # }

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
        items:list[CacheItem] = []
        for abs_path in abs_paths:
            # 获取相对路径
            rel_path = os.path.relpath(abs_path, self.input_path)

            # 数据处理
            with open(abs_path, "r", encoding = "utf-8-sig") as reader:
                json_data: dict[str, str] = json.load(reader)

                # 格式校验
                if not isinstance(json_data, dict):
                    continue

                # 读取数据
                for k, v in json_data.items():
                    if isinstance(k, str) and isinstance(v, str):
                        src = k
                        dst = v
                        if src == "":
                            items.append(
                                CacheItem({
                                    "src": src,
                                    "dst": dst,
                                    "row": len(items),
                                    "file_type": CacheItem.FileType.KVJSON,
                                    "file_path": rel_path,
                                    "status": Base.TranslationStatus.EXCLUDED,
                                })
                            )
                        elif dst != "" and src != dst:
                            items.append(
                                CacheItem({
                                    "src": src,
                                    "dst": dst,
                                    "row": len(items),
                                    "file_type": CacheItem.FileType.KVJSON,
                                    "file_path": rel_path,
                                    "status": Base.TranslationStatus.TRANSLATED_IN_PAST,
                                })
                            )
                        else:
                            items.append(
                                CacheItem({
                                    "src": src,
                                    "dst": dst,
                                    "row": len(items),
                                    "file_type": CacheItem.FileType.KVJSON,
                                    "file_path": rel_path,
                                    "status": Base.TranslationStatus.UNTRANSLATED,
                                })
                            )

        return items