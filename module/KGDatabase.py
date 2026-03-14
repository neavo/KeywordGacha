import json
import os
import sqlite3
import threading

from base.Base import Base
from model.Item import Item
from model.Project import Project

class KGDatabase(Base):

    def __init__(self) -> None:
        super().__init__()

        self.db_path: str = ""
        self.conn: sqlite3.Connection = None
        self.lock: threading.RLock = threading.RLock()

    def open(self, output_folder: str) -> None:
        with self.lock:
            folder = f"{output_folder}/cache"
            os.makedirs(folder, exist_ok = True)
            self.db_path = f"{folder}/cache.db"
            self.conn = sqlite3.connect(self.db_path, check_same_thread = False)
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.ensure_schema()

    def close(self) -> None:
        with self.lock:
            if self.conn is not None:
                self.conn.close()
                self.conn = None

    def is_open(self) -> bool:
        with self.lock:
            return self.conn is not None

    def ensure_schema(self) -> None:
        with self.lock:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
                CREATE TABLE IF NOT EXISTS project (
                    id INTEGER PRIMARY KEY,
                    data TEXT
                );
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT,
                    status TEXT,
                    data TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_items_file_path ON items(file_path);
                CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
            """)

    # ========== Meta ==========

    def get_meta(self, key: str, default: str = None) -> str:
        with self.lock:
            cursor = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_meta(self, key: str, value: str) -> None:
        with self.lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                (key, value),
            )
            self.conn.commit()

    # ========== Project ==========

    def get_project(self) -> Project:
        with self.lock:
            cursor = self.conn.execute("SELECT data FROM project WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return Project.from_dict(json.loads(row[0]))
            return Project()

    def set_project(self, project: Project) -> None:
        with self.lock:
            data = json.dumps(project.to_dict(), ensure_ascii = False)
            self.conn.execute(
                "INSERT OR REPLACE INTO project (id, data) VALUES (1, ?)",
                (data,),
            )
            self.conn.commit()

    # ========== Items ==========

    def get_all_items(self) -> list[Item]:
        with self.lock:
            cursor = self.conn.execute("SELECT data FROM items ORDER BY id")
            return [Item.from_dict(json.loads(row[0])) for row in cursor.fetchall()]

    def get_item_count(self) -> int:
        with self.lock:
            cursor = self.conn.execute("SELECT COUNT(*) FROM items")
            return cursor.fetchone()[0]

    def set_items(self, items: list[Item]) -> None:
        with self.lock:
            self.conn.execute("DELETE FROM items")
            self.conn.executemany(
                "INSERT INTO items (file_path, status, data) VALUES (?, ?, ?)",
                [
                    (
                        item.get_file_path(),
                        item.get_status(),
                        json.dumps(item.to_dict(), ensure_ascii = False),
                    )
                    for item in items
                ],
            )
            self.conn.commit()

    def update_items(self, items: list[Item], id_offset: int, indices: list[int]) -> None:
        """根据 items 在列表中的索引（对应数据库行 id = index + id_offset）批量更新"""
        with self.lock:
            self.conn.executemany(
                "UPDATE items SET file_path = ?, status = ?, data = ? WHERE id = ?",
                [
                    (
                        item.get_file_path(),
                        item.get_status(),
                        json.dumps(item.to_dict(), ensure_ascii = False),
                        idx + id_offset,
                    )
                    for item, idx in zip(items, indices)
                ],
            )
            self.conn.commit()

    def get_id_offset(self) -> int:
        """获取第一行的 id，用于计算 index → id 映射"""
        with self.lock:
            cursor = self.conn.execute("SELECT MIN(id) FROM items")
            row = cursor.fetchone()
            return row[0] if row[0] is not None else 1

    # ========== Workbench ==========

    def get_file_summary(self) -> list[dict]:
        """按文件分组统计"""
        with self.lock:
            cursor = self.conn.execute("""
                SELECT
                    file_path,
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN (?, ?) THEN 1 ELSE 0 END) as processed,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as excluded
                FROM items
                GROUP BY file_path
                ORDER BY MIN(id)
            """, (
                Base.ProjectStatus.PROCESSED,
                Base.ProjectStatus.PROCESSED_IN_PAST,
                Base.ProjectStatus.EXCLUDED,
            ))
            return [
                {
                    "file_path": row[0],
                    "total": row[1],
                    "processed": row[2],
                    "excluded": row[3],
                }
                for row in cursor.fetchall()
            ]

    def get_total_stats(self) -> dict:
        """获取全局统计"""
        with self.lock:
            cursor = self.conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN (?, ?) THEN 1 ELSE 0 END) as processed,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as excluded
                FROM items
            """, (
                Base.ProjectStatus.PROCESSED,
                Base.ProjectStatus.PROCESSED_IN_PAST,
                Base.ProjectStatus.EXCLUDED,
            ))
            row = cursor.fetchone()
            return {
                "total": row[0] or 0,
                "processed": row[1] or 0,
                "excluded": row[2] or 0,
            }
