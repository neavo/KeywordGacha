from typing import Callable

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from qfluentwidgets import CardWidget
from qfluentwidgets import CaptionLabel
from qfluentwidgets import StrongBodyLabel

class EmptyCard(CardWidget):

    def __init__(self, title: str, description: str, init: Callable = None) -> None:
        super().__init__(None)

        # 设置容器
        self.setBorderRadius(4)
        self.root = QHBoxLayout(self)
        self.root.setContentsMargins(16, 16, 16, 16) # 左、上、右、下

        # 文本控件
        self.vbox = QVBoxLayout()
        self.root.addLayout(self.vbox)

        self.title_label = StrongBodyLabel(title, self)
        self.vbox.addWidget(self.title_label)

        self.description_label = CaptionLabel(description, self)
        self.description_label.setTextColor(QColor(96, 96, 96), QColor(160, 160, 160))
        self.vbox.addWidget(self.description_label)

        # 填充
        self.root.addStretch(1)

        if callable(init):
            init(self)

    def get_title_label(self) -> StrongBodyLabel:
        return self.title_label

    def get_description_label(self) -> CaptionLabel:
        return self.description_label

    def add_widget(self, widget) -> None:
        self.root.addWidget(widget)

    def add_spacing(self, space: int) -> None:
        self.root.addSpacing(space)

    def remove_title(self) -> None:
        self.vbox.removeWidget(self.title_label)