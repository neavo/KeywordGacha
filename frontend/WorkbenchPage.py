import threading

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import Action
from qfluentwidgets import CaptionLabel
from qfluentwidgets import FluentIcon
from qfluentwidgets import FluentWindow
from qfluentwidgets import SimpleCardWidget
from qfluentwidgets import StrongBodyLabel
from qfluentwidgets import TableWidget

from widget.CommandBarCard import CommandBarCard

from base.Base import Base
from module.CacheManager import CacheManager
from module.Config import Config
from module.Engine.Engine import Engine
from module.Localizer.Localizer import Localizer


class StatCard(SimpleCardWidget):

    CARD_HEIGHT: int = 140

    def __init__(self, title: str, unit: str, accent_color: str = None, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.title_label = CaptionLabel(title, self)
        self.value_label = StrongBodyLabel("0", self)
        self.unit_label = CaptionLabel(unit, self)

        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        font = self.value_label.font()
        font.setPointSize(32)
        self.value_label.setFont(font)

        if isinstance(accent_color, str) and accent_color:
            accent = QColor(accent_color)
            if accent.isValid():
                self.value_label.setTextColor(accent, accent)

        self.unit_label.setTextColor(
            QColor(0, 0, 0, 115),
            QColor(255, 255, 255, 140),
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()
        layout.addWidget(self.unit_label)

        self.setFixedHeight(self.CARD_HEIGHT)

    def set_value(self, value: int) -> None:
        self.value_label.setText(f"{value:,}")


class WorkbenchPage(QWidget, Base):

    REFRESH_THROTTLE_MS: int = 500

    def __init__(self, text: str, window: FluentWindow) -> None:
        super().__init__(window)
        self.setObjectName(text.replace(" ", "-"))

        # 刷新控制
        self.refresh_pending: bool = False
        self.refresh_running: bool = False
        self.refresh_lock = threading.Lock()

        # 缓存管理器引用（使用 NERAnalyzer 的实例）
        self.cache_manager: CacheManager = None

        # 主容器
        self.container = QVBoxLayout(self)
        self.container.setSpacing(8)
        self.container.setContentsMargins(24, 24, 24, 24)

        # 构建 UI
        self.build_stats_section(self.container)
        self.build_table_section(self.container)
        self.build_footer_section(self.container)

        # 节流刷新定时器
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self.on_refresh_timeout)

        # 注册事件
        self.subscribe(Base.Event.WORKBENCH_REFRESH, self.on_workbench_refresh)
        self.subscribe(Base.Event.NER_ANALYZER_DONE, self.on_task_done)

    # 页面显示事件
    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.request_refresh()

    def on_workbench_refresh(self, event: Base.Event, data: dict) -> None:
        if not self.isVisible():
            return

        # 节流：500ms 内只刷新一次
        if self.refresh_timer.isActive():
            return
        self.refresh_timer.start(self.REFRESH_THROTTLE_MS)

    def on_refresh_timeout(self) -> None:
        if not self.isVisible():
            return
        self.request_refresh()

    def on_task_done(self, event: Base.Event, data: dict) -> None:
        self.request_refresh()

    def request_refresh(self) -> None:
        start_worker = False
        with self.refresh_lock:
            self.refresh_pending = True
            if self.refresh_running:
                return
            self.refresh_running = True
            start_worker = True

        if start_worker:
            threading.Thread(target = self.refresh_worker, daemon = True).start()

    def refresh_worker(self) -> None:
        while True:
            with self.refresh_lock:
                if not self.refresh_pending:
                    self.refresh_running = False
                    return
                self.refresh_pending = False

            # 获取缓存管理器
            cache_manager = self.get_cache_manager()
            if cache_manager is None:
                with self.refresh_lock:
                    self.refresh_running = False
                return

            # 从数据库获取统计数据
            try:
                file_summary = cache_manager.get_file_summary()
                total_stats = cache_manager.get_total_stats()
            except Exception:
                file_summary = []
                total_stats = {"total": 0, "processed": 0, "excluded": 0}

            # 在主线程更新 UI
            QTimer.singleShot(0, lambda fs=file_summary, ts=total_stats: self.apply_snapshot(fs, ts))

    def get_cache_manager(self) -> CacheManager:
        try:
            engine = Engine.get()
            if hasattr(engine, "ner_analayzer") and hasattr(engine.ner_analayzer, "cache_manager"):
                cm = engine.ner_analayzer.cache_manager
                if cm.db.is_open():
                    return cm
        except Exception:
            pass

        # 尝试临时打开数据库读取
        try:
            config = Config().load()
            cm = CacheManager(service = False)
            cm.open_database(config.output_folder)
            return cm
        except Exception:
            pass

        return None

    def apply_snapshot(self, file_summary: list[dict], total_stats: dict) -> None:
        total = total_stats.get("total", 0)
        processed = total_stats.get("processed", 0)
        excluded = total_stats.get("excluded", 0)
        remaining = total - processed - excluded

        self.card_files.set_value(len(file_summary))
        self.card_total.set_value(total)
        self.card_processed.set_value(processed)
        self.card_remaining.set_value(max(0, remaining))

        # 更新表格
        self.table.setRowCount(0)
        if len(file_summary) == 0:
            self.table.setRowCount(1)
            from PyQt5.QtWidgets import QTableWidgetItem
            item = QTableWidgetItem(Localizer.get().workbench_no_data)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(0, 0, item)
            self.table.setSpan(0, 0, 1, 4)
        else:
            from PyQt5.QtWidgets import QTableWidgetItem
            self.table.setRowCount(len(file_summary))
            for row, entry in enumerate(file_summary):
                file_total = entry.get("total", 0)
                file_processed = entry.get("processed", 0)
                file_excluded = entry.get("excluded", 0)
                file_remaining = file_total - file_processed - file_excluded

                path_item = QTableWidgetItem(entry.get("file_path", ""))
                total_item = QTableWidgetItem(str(file_total))
                processed_item = QTableWidgetItem(str(file_processed))
                remaining_item = QTableWidgetItem(str(max(0, file_remaining)))

                total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                processed_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.table.setItem(row, 0, path_item)
                self.table.setItem(row, 1, total_item)
                self.table.setItem(row, 2, processed_item)
                self.table.setItem(row, 3, remaining_item)

    def build_stats_section(self, parent: QLayout) -> None:
        stats_frame = QFrame(self)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(12)

        self.card_files = StatCard(
            Localizer.get().workbench_stat_files,
            Localizer.get().workbench_unit_file,
        )
        self.card_total = StatCard(
            Localizer.get().workbench_stat_total,
            Localizer.get().workbench_unit_line,
        )
        self.card_processed = StatCard(
            Localizer.get().workbench_stat_processed,
            Localizer.get().workbench_unit_line,
            accent_color = "#22c55e",
        )
        self.card_remaining = StatCard(
            Localizer.get().workbench_stat_remaining,
            Localizer.get().workbench_unit_line,
            accent_color = "#f59e0b",
        )

        for card in (self.card_files, self.card_total, self.card_processed, self.card_remaining):
            stats_layout.addWidget(card)

        parent.addWidget(stats_frame)

    def build_table_section(self, parent: QLayout) -> None:
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            Localizer.get().workbench_col_file_path,
            Localizer.get().workbench_col_total,
            Localizer.get().workbench_col_processed,
            Localizer.get().workbench_col_remaining,
        ])

        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)

        # 只读
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # 隐藏垂直表头
        self.table.verticalHeader().hide()

        parent.addWidget(self.table, 1)

    def build_footer_section(self, parent: QLayout) -> None:
        self.command_bar_card = CommandBarCard()

        def on_export_translation() -> None:
            self.emit(Base.Event.NER_ANALYZER_EXPORT, {})

        self.command_bar_card.add_action(
            Action(FluentIcon.SHARE, Localizer.get().workbench_export_translation, self, triggered = on_export_translation),
        )

        parent.addWidget(self.command_bar_card)
