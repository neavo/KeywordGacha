import json
import os
import threading
import time

from base.Base import Base
from model.Project import Project
from model.Item import Item
from module.Localizer.Localizer import Localizer

class CacheManager(Base):

    # 缓存文件保存周期（秒）
    SAVE_INTERVAL = 15

    # 类线程锁
    LOCK = threading.Lock()

    def __init__(self, service: bool) -> None:
        super().__init__()

        # 默认值
        self.project: Project = Project()
        self.items: list[Item] = []

        # 初始化
        self.require_flag: bool = False
        self.require_path: str = ""
        self.last_require_time: float = 0

        # 启动定时任务
        if service == True:
            threading.Thread(target = self.task).start()

    # 保存缓存到文件的定时任务
    def task(self) -> None:
        while True:
            # 休眠 1 秒
            time.sleep(1.00)

            if (
                time.time() - self.last_require_time >= __class__.SAVE_INTERVAL
                and self.require_flag == True
            ):
                # 创建上级文件夹
                folder_path = f"{self.require_path}/cache"
                os.makedirs(folder_path, exist_ok = True)

                # 保存缓存到文件
                self.save_to_file(
                    project = self.project,
                    items = self.items,
                    output_folder = self.require_path,
                )

                # 触发事件
                self.emit(Base.Event.CACHE_SAVE, {})

                # 重置标志
                self.require_flag = False
                self.last_require_time = time.time()

    # 保存缓存到文件
    def save_to_file(self, project: Project, items: list[Item], output_folder: str) -> None:
        # 创建上级文件夹
        os.makedirs(f"{output_folder}/cache", exist_ok = True)

        # 保存缓存到文件
        path = f"{output_folder}/cache/items.json"
        with __class__.LOCK:
            try:
                with open(path, "w", encoding = "utf-8") as writer:
                    writer.write(json.dumps([item.to_dict() for item in items], indent = None, ensure_ascii = False))
            except Exception as e:
                self.debug(Localizer.get().log_write_file_fail, e)

        # 保存项目数据到文件
        path = f"{output_folder}/cache/project.json"
        with __class__.LOCK:
            try:
                with open(path, "w", encoding = "utf-8") as writer:
                    writer.write(json.dumps(project.to_dict(), indent = None, ensure_ascii = False))
            except Exception as e:
                self.debug(Localizer.get().log_write_file_fail, e)

        # 重置标志
        self.require_flag = False
        self.last_require_time = time.time()

    # 请求保存缓存到文件
    def require_save_to_file(self, output_path: str) -> None:
        self.require_flag = True
        self.require_path = output_path

    # 从文件读取数据
    def load_from_file(self, output_path: str) -> None:
        self.load_items_from_file(output_path)
        self.load_project_from_file(output_path)

    # 从文件读取项目数据
    def load_items_from_file(self, output_path: str) -> None:
        path = f"{output_path}/cache/items.json"
        with __class__.LOCK:
            try:
                if os.path.isfile(path):
                    with open(path, "r", encoding = "utf-8-sig") as reader:
                        self.items = [Item.from_dict(item) for item in json.load(reader)]
            except Exception as e:
                self.debug(Localizer.get().log_read_file_fail, e)

    # 从文件读取项目数据
    def load_project_from_file(self, output_path: str) -> None:
        path = f"{output_path}/cache/project.json"
        with __class__.LOCK:
            try:
                if os.path.isfile(path):
                    with open(path, "r", encoding = "utf-8-sig") as reader:
                        self.project = Project.from_dict(json.load(reader))
            except Exception as e:
                self.debug(Localizer.get().log_read_file_fail, e)

    # 设置缓存数据
    def set_items(self, items: list[Item]) -> None:
        self.items = items

    # 获取缓存数据
    def get_items(self) -> list[Item]:
        return self.items

    # 设置项目数据
    def set_project(self, project: Project) -> None:
        self.project = project

    # 获取项目数据
    def get_project(self) -> Project:
        return self.project

    # 获取缓存数据数量
    def get_item_count(self) -> int:
        return len(self.items)

    # 复制缓存数据
    def copy_items(self) -> list[Item]:
        return [Item.from_dict(item.to_dict()) for item in self.items]

    # 获取缓存数据数量（根据翻译状态）
    def get_item_count_by_status(self, status: int) -> int:
        return len([item for item in self.items if item.get_status() == status])

    # 生成缓存数据条目片段
    def generate_item_chunks(self, token_threshold: int) -> list[list[Item]]:
        # 根据 Token 阈值计算行数阈值，避免大量短句导致行数太多
        line_limit = max(8, int(token_threshold / 16))

        skip: int = 0
        line_length: int = 0
        token_length: int = 0
        chunk: list[Item] = []
        chunks: list[list[Item]] = []
        for item in self.items:
            # 跳过状态不是 未翻译 的数据
            if item.get_status() != Base.ProjectStatus.NONE:
                skip = skip + 1
                continue

            # 每个片段的第一条不判断是否超限，以避免特别长的文本导致死循环
            current_line_length = sum(1 for line in item.get_src().splitlines() if line.strip())
            current_token_length = item.get_token_count()
            if len(chunk) == 0:
                pass
            # 如果 行数超限、Token 超限、数据来源跨文件，则结束此片段
            elif (
                line_length + current_line_length > line_limit
                or token_length + current_token_length > token_threshold
                or item.get_file_path() != chunk[-1].get_file_path()
            ):
                chunks.append(chunk)
                skip = 0

                chunk = []
                line_length = 0
                token_length = 0

            chunk.append(item)
            line_length = line_length + current_line_length
            token_length = token_length + current_token_length

        # 如果还有剩余数据，则添加到列表中
        if len(chunk) > 0:
            chunks.append(chunk)
            skip = 0

        return chunks