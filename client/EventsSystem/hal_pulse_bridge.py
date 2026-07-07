"""Qt-сигналы состояния импульсов LOCK/SOL для синхронизации UI."""

from PyQt5.QtCore import QObject, pyqtSignal


class HalPulseBridge(QObject):
    """Уведомляет экраны об изменении active/pending по каналу lock | sol."""

    state_changed = pyqtSignal(str, bool, bool)  # channel, active, pending
