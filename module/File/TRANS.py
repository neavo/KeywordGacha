import json

class TRANS():

    def __init__(self) -> None:
        super().__init__()

    # 读取
    def read_from_path(self, abs_paths: list[str]) -> list[str]:
        items: list[str] = []
        for abs_path in set(abs_paths):
            # 数据处理
            with open(abs_path, "r", encoding = "utf-8-sig") as reader:
                json_data = json.load(reader)

                # 有效性校验
                if not isinstance(json_data, dict):
                    continue

                # 获取项目信息
                project: dict = json_data.get("project", {})

                # 处理数据
                for path, entry in project.get("files", {}).items():
                    for data in entry.get("data", []):
                        # 有效性校验
                        if not isinstance(data, list) or len(data) == 0 or not isinstance(data[0], str):
                            continue

                        # 添加数据
                        items.append(data[0])

        return items
