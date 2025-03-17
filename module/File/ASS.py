class ASS():

    # [Script Info]
    # ; This is an Advanced Sub Station Alpha v4+ script.
    # Title:
    # ScriptType: v4.00+
    # PlayDepth: 0
    # ScaledBorderAndShadow: Yes

    # [V4+ Styles]
    # Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
    # Style: Default,Arial,20,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,1,2,10,10,10,1

    # [Events]
    # Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
    # Dialogue: 0,0:00:08.12,0:00:10.46,Default,,0,0,0,,にゃにゃにゃ
    # Dialogue: 0,0:00:14.00,0:00:15.88,Default,,0,0,0,,えーこの部屋一人で使\Nえるとか最高じゃん
    # Dialogue: 0,0:00:15.88,0:00:17.30,Default,,0,0,0,,えるとか最高じゃん

    def __init__(self) -> None:
        super().__init__()

    # 读取
    def read_from_path(self, abs_paths: list[str]) -> list[str]:
        items: list[str] = []
        for abs_path in set(abs_paths):
            # 数据处理
            with open(abs_path, "r", encoding = "utf-8-sig") as reader:
                lines = [line.strip() for line in reader.readlines()]

                # 格式字段的数量
                in_event = False
                format_field_num = -1
                for line in lines:
                    # 判断是否进入事件块
                    if line == "[Events]":
                        in_event = True
                    # 在事件块中寻找格式字段
                    if in_event == True and line.startswith("Format:"):
                        format_field_num = len(line.split(",")) - 1
                        break

                for line in lines:
                    content = ",".join(line.split(",")[format_field_num:]) if line.startswith("Dialogue:") else ""

                    # 添加数据
                    items.append(content.replace("\\N", "\n"))

        return items