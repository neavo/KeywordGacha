import json

class MESSAGEJSON():

    # [
    #     {
    #         "name", "しますか",
    #         "message": "<fgName:pipo-fog004><fgLoopX:1><fgLoopY:1><fgSx:-2><fgSy:0.5>"
    #     },
    #     {
    #         "message": "エンディングを変更しますか？"
    #     },
    #     {
    #         "message": "はい"
    #     },
    # ]

    def __init__(self) -> None:
        super().__init__()

    # 读取名称和数据
    def read_from_path(self, abs_paths: list[str]) -> list[str]:
        items: list[str] = []
        for abs_path in set(abs_paths):
            # 数据处理
            with open(abs_path, "r", encoding = "utf-8-sig") as reader:
                json_data: list[dict[str, dict]] = json.load(reader)

                # 格式校验
                if not isinstance(json_data, list):
                    continue

                for v in json_data:
                    if not isinstance(v, dict) or "message" not in v:
                        continue

                    if "name" not in v:
                        items.append(v.get("message", ""))
                    elif isinstance(v.get("name"), str):
                        items.append(f"【{v.get("name")}】{v.get("message", "")}")
                    else:
                        items.append(v.get("message", ""))

        return items