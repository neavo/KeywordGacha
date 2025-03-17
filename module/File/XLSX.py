import openpyxl

class XLSX():

    def __init__(self) -> None:
        super().__init__()

    # 读取
    def read_from_path(self, abs_paths: list[str]) -> list[str]:
        items: list[str] = []
        for abs_path in set(abs_paths):
            # 数据处理
            wb = openpyxl.load_workbook(abs_path)
            sheet = wb.active

            # 跳过空表格
            if sheet.max_row == 0 or sheet.max_column == 0:
                continue

            for row in range(1, sheet.max_row + 1):
                src = sheet.cell(row = row, column = 1).value
                dst = sheet.cell(row = row, column = 2).value

                # 跳过读取失败的行
                # 数据不存在时为 None，存在时可能是 str int float 等多种类型
                if src is None:
                    continue

                src = str(src)
                dst = str(dst) if dst is not None else ""
                if src == "":
                    items.append(src)
                elif dst != "" and src != dst:
                    items.append(src)
                else:
                    items.append(src)

        return items