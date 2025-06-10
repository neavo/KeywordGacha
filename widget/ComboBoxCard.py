from typing import Callable

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from qfluentwidgets import CardWidget
from qfluentwidgets import ComboBox
from qfluentwidgets import CaptionLabel
from qfluentwidgets import StrongBodyLabel

class ComboBoxCard(CardWidget):

    def __init__(self, title: str, description: str, items: list, init: Callable = None, current_changed: Callable = None) -> None:
        super().__init__(None)

        # 设置容器
        self.setBorderRadius(4)
        self.hbox = QHBoxLayout(self)
        self.hbox.setContentsMargins(16, 16, 16, 16) # 左、上、右、下

        # 文本控件
        self.vbox = QVBoxLayout()

        self.title_label = StrongBodyLabel(title, self)
        self.description_label = CaptionLabel(description, self)
        self.description_label.setTextColor(QColor(96, 96, 96), QColor(160, 160, 160))

        self.vbox.addWidget(self.title_label)
        self.vbox.addWidget(self.description_label)
        self.hbox.addLayout(self.vbox)

        # 填充
        self.hbox.addStretch(1)

        # 下拉框控件
        self.combo_box = ComboBox(self)
        self.combo_box.addItems(items)
        self.hbox.addWidget(self.combo_box)

        if callable(init):
            init(self)

        if callable(current_changed):
            self.combo_box.currentIndexChanged.connect(lambda _: current_changed(self))

    def get_combo_box(self) -> ComboBox:
        return self.combo_box