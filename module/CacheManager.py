import json
import os
import threading

from base.Base import Base
from model.Project import Project
from model.Item import Item
from module.KGDatabase import KGDatabase
from module.Localizer.Localizer import Localizer

class CacheManager(Base):

    # 类线程锁
    LOCK = threading.Lock()

    def __init__(self, service: bool) -> None:
        super().__init__()

        # 默认值
        self.project: Project = Project()
        self.items: list[Item] = []

        # 数据库实例
        self.db: KGDatabase = KGDatabase()

        # items 在内存列表中的 index 与数据库 id 的偏移量
        self.id_offset: int = 1

    # 打开数据库
    def open_database(self, output_folder: str) -> None:
        self.db.open(output_folder)

        # 兼容旧版本 JSON 缓存：如果有 JSON 文件但数据库为空，则迁移
        self.migrate_from_json(output_folder)

    # 关闭数据库
    def close_database(self) -> None:
        self.db.close()

    # 从旧版 JSON 缓存迁移到 SQLite
    def migrate_from_json(self, output_folder: str) -> None:
        items_path = f"{output_folder}/cache/items.json"
        project_path = f"{output_folder}/cache/project.json"

        if not os.path.isfile(items_path):
            return

        # 数据库已有数据则不迁移
        if self.db.get_item_count() > 0:
            return

        try:
            # 读取 JSON 数据
            with open(items_path, "r", encoding = "utf-8-sig") as reader:
                items = [Item.from_dict(item) for item in json.load(reader)]

            project = Project()
            if os.path.isfile(project_path):
                with open(project_path, "r", encoding = "utf-8-sig") as reader:
                    project = Project.from_dict(json.load(reader))

            # 写入 SQLite
            self.db.set_items(items)
            self.db.set_project(project)

            # 迁移成功后删除 JSON 文件
            os.remove(items_path)
            if os.path.isfile(project_path):
                os.remove(project_path)

            self.info(Localizer.get().log_cache_migrated)
        except Exception as e:
            self.debug(Localizer.get().log_read_file_fail, e)

    # 将所有数据保存到数据库
    def save_to_database(self) -> None:
        if not self.db.is_open():
            return

        try:
            self.db.set_items(self.items)
            self.db.set_project(self.project)
            self.id_offset = self.db.get_id_offset()
        except Exception as e:
            self.debug(Localizer.get().log_write_file_fail, e)

    # 保存项目数据到数据库
    def save_project_to_database(self) -> None:
        if not self.db.is_open():
            return

        try:
            self.db.set_project(self.project)
        except Exception as e:
            self.debug(Localizer.get().log_write_file_fail, e)

    # 立即保存一批已处理的 items 到数据库
    def save_items_immediate(self, items: list[Item]) -> None:
        if not self.db.is_open():
            return

        try:
            # 计算每个 item 在内存列表中的 index
            item_set = set(id(item) for item in items)
            indices = [i for i, item in enumerate(self.items) if id(item) in item_set]

            if indices:
                batch_items = [self.items[i] for i in indices]
                self.db.update_items(batch_items, self.id_offset, indices)

            # 同时保存项目进度
            self.db.set_project(self.project)
        except Exception as e:
            self.debug(Localizer.get().log_write_file_fail, e)

    # 兼容旧接口 - 保存到文件（现在保存到数据库）
    def save_to_file(self, project: Project, items: list[Item], output_folder: str) -> None:
        if not self.db.is_open():
            self.open_database(output_folder)
        self.save_to_database()

    # 兼容旧接口 - 请求保存（现在立即保存项目）
    def require_save_to_file(self, output_path: str) -> None:
        # 不再需要延时，由 save_items_immediate 在回调中立即保存
        pass

    # 从数据库读取数据
    def load_from_database(self, output_folder: str) -> None:
        if not self.db.is_open():
            self.open_database(output_folder)

        self.items = self.db.get_all_items()
        self.project = self.db.get_project()
        self.id_offset = self.db.get_id_offset()

    # 兼容旧接口 - 从文件读取
    def load_from_file(self, output_path: str) -> None:
        self.load_from_database(output_path)

    # 兼容旧接口 - 只加载项目数据
    def load_project_from_file(self, output_path: str) -> None:
        if not self.db.is_open():
            self.open_database(output_path)

        # 检查数据库是否有数据
        if self.db.get_item_count() > 0:
            self.project = self.db.get_project()
        else:
            # 回退到 JSON（可能尚未迁移）
            project_path = f"{output_path}/cache/project.json"
            if os.path.isfile(project_path):
                try:
                    with open(project_path, "r", encoding = "utf-8-sig") as reader:
                        self.project = Project.from_dict(json.load(reader))
                except Exception as e:
                    self.debug(Localizer.get().log_read_file_fail, e)

        self.close_database()

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

    # 删除指定文件的所有数据
    def delete_file(self, file_path: str) -> int:
        # 从内存中移除
        self.items = [item for item in self.items if item.get_file_path() != file_path]
        # 从数据库中删除
        if self.db.is_open():
            return self.db.delete_items_by_file_path(file_path)
        return 0

    # 获取工作台文件摘要
    def get_file_summary(self) -> list[dict]:
        if self.db.is_open():
            return self.db.get_file_summary()
        return []

    # 获取全局统计
    def get_total_stats(self) -> dict:
        if self.db.is_open():
            return self.db.get_total_stats()
        return {"total": 0, "processed": 0, "excluded": 0}

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
