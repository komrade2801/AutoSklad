"""Единый вид кнопки «Назад»: оранжевая, скруглённая, на всю ширину с полями."""

from PyQt5 import QtCore, QtGui, QtWidgets

# Как у основных кнопок экранов (screen_37, screen_38, …)
BACK_BUTTON_STYLE = """
QPushButton#btn_back {
    color: #FFFFFF;
    background-color: #f09022;
    border: none;
    border-radius: 8px;
    font-family: "Roboto", Sans-serif;
    font-size: 20px;
    font-weight: 600;
    min-height: 50px;
    max-height: 50px;
}
QPushButton#btn_back:pressed {
    background-color: #d97f1e;
}
QPushButton#btn_back:disabled {
    background-color: #a06830;
    color: #cccccc;
}
"""

def style_back_button(btn: QtWidgets.QPushButton) -> None:
    """Оранжевый фон, скругление 8px, иконка «назад»."""
    btn.setObjectName("btn_back")
    btn.setText("")
    btn.setMinimumHeight(50)
    btn.setMaximumHeight(50)
    btn.setSizePolicy(
        QtWidgets.QSizePolicy.Expanding,
        QtWidgets.QSizePolicy.Fixed,
    )
    btn.setStyleSheet(BACK_BUTTON_STYLE)
    btn.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
    btn.setLayoutDirection(QtCore.Qt.LeftToRight)
    btn.setCursor(QtCore.Qt.PointingHandCursor)
    icon = QtGui.QIcon()
    icon.addPixmap(
        QtGui.QPixmap(":/icons/back_white.png"),
        QtGui.QIcon.Normal,
        QtGui.QIcon.Off,
    )
    btn.setIcon(icon)
    btn.setIconSize(QtCore.QSize(51, 51))


def create_back_button(parent: QtWidgets.QWidget) -> QtWidgets.QPushButton:
    btn = QtWidgets.QPushButton(parent)
    style_back_button(btn)
    return btn


def add_back_button_row(
    layout: QtWidgets.QVBoxLayout,
    parent: QtWidgets.QWidget,
) -> QtWidgets.QPushButton:
    """
    Кнопка «Назад» внизу на всю ширину контентной области.
    Отступы от краёв экрана — через setContentsMargins корневого layout экрана (обычно 12–16 px).
    """
    btn = create_back_button(parent)
    layout.addWidget(btn)
    return btn
