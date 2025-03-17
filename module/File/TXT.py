import os

class TXT():

    def __init__(self) -> None:
        super().__init__()

    # 读取
    def read_from_path(self, abs_paths: list[str]) -> list[str]:
        items: list[str] = []
        for abs_path in set(abs_paths):
            # 数据处理
            with open(abs_path, "r", encoding = "utf-8-sig") as reader:
                for line in [line.removesuffix("\n") for line in reader.readlines()]:
                    items.append(line)

        return items