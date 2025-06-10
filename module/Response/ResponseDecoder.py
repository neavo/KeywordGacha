import json_repair as repair

from base.Base import Base

class ResponseDecoder(Base):

    def __init__(self) -> None:
        super().__init__()

    # 解析文本
    def decode(self, response: str) -> tuple[list[str], list[dict[str, str]]]:
        dsts: list[str] = []
        glossary: list[dict[str, str]] = []

        # 按行解析失败时，尝试按照普通 JSON 字典进行解析
        for line in response.splitlines():
            json_data = repair.loads(line)
            if isinstance(json_data, dict):
                if all(v in json_data for v in ("src", "dst", "type")):
                    src: str = json_data.get("src")
                    dst: str = json_data.get("dst")
                    type: str = json_data.get("type")
                    glossary.append(
                        {
                            "src": src if isinstance(src, str) else "",
                            "dst": dst if isinstance(dst, str) else "",
                            "info": type if isinstance(type, str) else "",
                        }
                    )

        # 返回默认值
        return dsts, glossary