import re
import time

import rich
from rich import box
from rich import markup
from rich.table import Table

from base.Base import Base
from base.LogManager import LogManager
from model.Item import Item
from module.Config import Config
from module.Engine.TaskRequester import TaskRequester
from module.FakeNameHelper import FakeNameHelper
from module.Localizer.Localizer import Localizer
from module.Normalizer import Normalizer
from module.PromptBuilder import PromptBuilder
from module.Response.ResponseDecoder import ResponseDecoder
from module.RubyCleaner import RubyCleaner

class NERAnalyzerTask(Base):

    def __init__(self, config: Config, platform: dict, items: list[Item]) -> None:
        super().__init__()

        # 初始化
        self.items = items
        self.config = config
        self.platform = platform
        self.prompt_builder = PromptBuilder(self.config)

    # 启动任务
    def start(self) -> dict[str, str]:
        return self.request(self.items)

    # 请求
    def request(self, items: list[Item]) -> dict[str, str]:
        # 任务开始的时间
        start_time = time.time()

        # 文本预处理
        srcs: list[str] = []
        for item in items:
            # 注入姓名
            if item.get_first_name_src() is not None:
                item.set_src(f"【{item.get_first_name_src()}】{item.get_src()}")

            # 拆分文本
            for src in item.get_src().split("\n"):
                # 正规化
                src = Normalizer.normalize(src)

                # 清理注音
                src = RubyCleaner.clean(src)

                # 前置替换
                src = self.pre_replacement(src)

                # 注入伪名
                src = FakeNameHelper.inject(src)

                if src == "":
                    pass
                elif src.strip() == "":
                    pass
                else:
                    srcs.append(src)

        # 如果没有任何有效原文文本，则直接完成当前任务
        if len(srcs) == 0:
            for item in items:
                item.set_dst(item.get_src())
                item.set_status(Base.ProjectStatus.PROCESSED)

            return {
                "glossary": [],
                "row_count": len(items),
                "input_tokens": 0,
                "output_tokens": 0,
            }

        # 生成请求提示词
        messages, console_log = self.prompt_builder.generate_prompt(srcs)

        # 发起请求
        requester = TaskRequester(self.config, self.platform)
        skip, response_think, response_result, input_tokens, output_tokens = requester.request(messages)

        # 如果请求结果标记为 skip，即有错误发生，则跳过本次循环
        if skip == True:
            return {
                "glossary": [],
                "row_count": 0,
                "input_tokens": 0,
                "output_tokens": 0,
            }

        # 提取回复内容
        _, glossary = ResponseDecoder().decode(response_result)

        # 模型回复日志
        # 在这里将日志分成打印在控制台和写入文件的两份，按不同逻辑处理
        file_log = console_log.copy()
        if response_think != "":
            file_log.append(Localizer.get().engine_response_think + "\n" + response_think)
            console_log.append(Localizer.get().engine_response_think + "\n" + response_think)
        if response_result != "":
            file_log.append(Localizer.get().engine_response_result + "\n" + response_result)
            console_log.append(Localizer.get().engine_response_result + "\n" + response_result) if LogManager.get().is_expert_mode() else None

        for item in items:
            item.set_status(Base.ProjectStatus.PROCESSED)

        # 打印任务结果
        self.print_log_table(
            start_time,
            input_tokens,
            output_tokens,
            [line.strip() for line in srcs],
            file_log,
            console_log
        )

        # 返回任务结果
        return {
            "glossary": glossary,
            "row_count": len(items),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    # 前置替换
    def pre_replacement(self, src: str) -> str:
        if self.config.pre_replacement_enable == False:
            return src

        for v in self.config.pre_replacement_data:
            if v.get("regex", False) != True:
                src = src.replace(v.get("src"), v.get("dst"))
            else:
                src = re.sub(rf"{v.get("src")}", rf"{v.get("dst")}", src)

        return src

    # 打印日志表格
    def print_log_table(self, start: int, input: int, output: int, srcs: list[str], file_log: list[str], console_log: list[str]) -> None:
        # 拼接错误原因文本
        style = "green"
        message = Localizer.get().engine_task_success.replace("{TIME}", f"{(time.time() - start):.2f}")
        message = message.replace("{LINES}", f"{len(srcs)}")
        message = message.replace("{PT}", f"{input}")
        message = message.replace("{CT}", f"{output}")
        log_func = self.info

        # 添加日志
        file_log.insert(0, message)
        console_log.insert(0, message)

        # 写入日志到文件
        file_rows = self.generate_log_rows(file_log)
        log_func("\n" + "\n\n".join(file_rows) + "\n", file = True, console = False)

        # 打印日志到控制台
        rich.get_console().print(
            self.generate_log_table(
                self.generate_log_rows(console_log),
                style,
            )
        )

    # 生成日志行
    def generate_log_rows(self, extra: list[str]) -> tuple[list[str], str]:
        rows = []

        # 添加额外日志
        for v in extra:
            rows.append(markup.escape(v.strip()))

        return rows

    # 生成日志表格
    def generate_log_table(self, rows: list, style: str) -> Table:
        table = Table(
            box = box.ASCII2,
            expand = True,
            title = " ",
            caption = " ",
            highlight = True,
            show_lines = True,
            show_header = False,
            show_footer = False,
            collapse_padding = True,
            border_style = style,
        )
        table.add_column("", style = "white", ratio = 1, overflow = "fold")

        for row in rows:
            if isinstance(row, str):
                table.add_row(row)
            else:
                table.add_row(*row)

        return table