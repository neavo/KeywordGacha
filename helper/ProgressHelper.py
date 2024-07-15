import re
from rich.progress import Progress
from rich.progress import BarColumn
from rich.progress import TextColumn
from rich.progress import TimeElapsedColumn
from rich.progress import TimeRemainingColumn

class ProgressHelper:

    # 获取一个进度条实例
    @staticmethod
    def get_progress(**kwargs):
        return Progress(
            TextColumn("{task.description}", justify = "right"),
            "•",
            BarColumn(bar_width = None),
            "•",
            TextColumn("{task.completed}/{task.total}", justify = "right"),
            "•",
            TimeElapsedColumn(),
            "/",
            TimeRemainingColumn(),
            **kwargs
        )