from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLayout
from PyQt5.QtWidgets import QVBoxLayout
from qfluentwidgets import FluentWindow
from qfluentwidgets import SingleDirectionScrollArea

from base.Base import Base
from module.Config import Config
from module.Localizer.Localizer import Localizer
from widget.SpinCard import SpinCard
from widget.SwitchButtonCard import SwitchButtonCard

class ExpertSettingsPage(QWidget, Base):

    def __init__(self, text: str, window: FluentWindow) -> None:
        super().__init__(window)
        self.setObjectName(text.replace(" ", "-"))

        # 载入并保存默认配置
        config = Config().load().save()

        # 设置容器
        self.root = QVBoxLayout(self)
        self.root.setSpacing(8)
        self.root.setContentsMargins(6, 24, 6, 24) # 左、上、右、下

        # 创建滚动区域的内容容器
        scroll_area_vbox_widget = QWidget()
        scroll_area_vbox = QVBoxLayout(scroll_area_vbox_widget)
        scroll_area_vbox.setContentsMargins(18, 0, 18, 0)

        # 创建滚动区域
        scroll_area = SingleDirectionScrollArea(orient = Qt.Orientation.Vertical)
        scroll_area.setWidget(scroll_area_vbox_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.enableTransparentBackground()

        # 将滚动区域添加到父布局
        self.root.addWidget(scroll_area)

        # 添加控件
        self.add_widget_output_choices(scroll_area_vbox, config, window)
        self.add_widget_output_kvjson(scroll_area_vbox, config, window)

        # 填充
        scroll_area_vbox.addStretch(1)

    # 输出候选数据
    def add_widget_output_choices(self, parent: QLayout, config: Config, windows: FluentWindow) -> None:

        def init(widget: SwitchButtonCard) -> None:
            widget.get_switch_button().setChecked(
                config.output_choices
            )

        def checked_changed(widget: SwitchButtonCard) -> None:
            config = Config().load()
            config.output_choices = widget.get_switch_button().isChecked()
            config.save()

        parent.addWidget(
            SwitchButtonCard(
                title = Localizer.get().expert_settings_page_output_choices_title,
                description = Localizer.get().expert_settings_page_output_choices_description,
                init = init,
                checked_changed = checked_changed,
            )
        )

    # 输出 KVJSON 文件
    def add_widget_output_kvjson(self, parent: QLayout, config: Config, windows: FluentWindow) -> None:

        def init(widget: SwitchButtonCard) -> None:
            widget.get_switch_button().setChecked(
                config.output_kvjson
            )

        def checked_changed(widget: SwitchButtonCard) -> None:
            config = Config().load()
            config.output_kvjson = widget.get_switch_button().isChecked()
            config.save()

        parent.addWidget(
            SwitchButtonCard(
                title = Localizer.get().expert_settings_page_output_kvjson_title,
                description = Localizer.get().expert_settings_page_output_kvjson_description,
                init = init,
                checked_changed = checked_changed,
            )
        )