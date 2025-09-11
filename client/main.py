import json
import sys
import traceback
import ast
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List
import os

import uvicorn
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from fastapi import FastAPI

from BarcodeScanner.serial_manager import SerialManager
from BarcodeScanner.MockSerialManager import MockSerialManager
from Core import platforms
from Core.sync_config import SyncConfig
from DB.Data.sqlite_db import SessionLocal
from EventsSystem.Executor import Executor
from GUI.MainWindow import MainWindow
from StateMachine.FMS import Maps
from StateMachine.converter_xml_2 import map_builder

from dbSync.Runner import start_sync, stop_sync
from dbSync.Transport.routers import sync_router


# ------------------------------------------------------------
# 1) Определяем lifespan для FastAPI: здесь читаем config.json,
#    запускаем sync-потоки и регистрируем stop_sync на shutdown.
# ------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = SyncConfig()

    # вы можете залогировать их, чтобы убедиться:
    print("SYNC CONFIG:", cfg.__dict__)

    start_sync(
        device_id=cfg.device_id,
        host=cfg.ip,
        port=cfg.port,
        token=cfg.token,
        secret=cfg.secret,
        aes=cfg.aes,
        scheduler_sender_timeout=cfg.sender_timeout,
        scheduler_receiver_timeout=cfg.receiver_timeout
    )
    yield
    stop_sync(cfg.device_id)

# ------------------------------------------------------------
# 2) Инициализируем FastAPI и монтируем роутер синхронизации
# ------------------------------------------------------------
app = FastAPI(title="API основного приложения",
              version="1.0", lifespan=lifespan)
app.mount("/sync", sync_router)


# ------------------------------------------------------------
# 3) QThread для запуска Uvicorn без блокировки GUI
# ------------------------------------------------------------
class UvicornThread(QThread):
    """
    Запускает Uvicorn в своём потоке, чтобы не блокировать Qt event loop.
    """
    finished = pyqtSignal()

    def __init__(self, ip: str, port: int, parent=None):
        super().__init__(parent)
        self.ip = ip
        self.port = port

    def run(self):
        # Здесь uvicorn.run блокирует до остановки процесса,
        # поэтому мы запускаем его внутри потока.
        uvicorn.run(app, host=self.ip, port=self.port, log_level="info")
        # Сигнал о завершении (если ever)
        self.finished.emit()


# ------------------------------------------------------------
# 4) Точка входа для GUI-приложения
# ------------------------------------------------------------
def main():
    # a) Билдим карты — подготовка FSM
    # d) Запускаем Uvicorn в фоне
    #    Бери host/port из config.json, как в lifespan
    cfg = json.loads(
        (Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
    map_builder()

    # b) Запускаем Qt-приложение
    qt_app = QApplication(sys.argv)

    # c) Настраиваем SerialManager/BarcodeManager
    use_mocks = os.getenv("AUTOSKLAD_USE_MOCKS", "0") == "1"
    current_platform = platforms.detect()
    if use_mocks:
        serial_manager = MockSerialManager(port=None)
        barcode_manager = MockSerialManager(port=None)
    else:
        if current_platform == platforms.Windows:
            serial = cfg["serial"]
            serial_manager = SerialManager(port=serial["port"])
            barcode = cfg["barcode"]
            barcode_manager = SerialManager(port=barcode["port"])
        else:  # Raspberry Pi и др.
            ports = cfg["dev"]
            serial_manager = SerialManager(port=ports["ttyUSB"])
            barcode_manager = SerialManager(port=ports["serial"])

    serial_manager.start()
    barcode_manager.start()

    opts = cfg["network"]
    host_ip = opts["ip"]
    port = int(opts["port"])

    uvicorn_thread = UvicornThread(ip=host_ip, port=port)
    uvicorn_thread.setObjectName("UvicornThread")
    uvicorn_thread.start()

    # e) Основная логика GUI
    maps = Maps('screen_1_welcome')
    window = MainWindow(maps)
    executor = Executor()
    executor.attach_serial_manager(serial_manager)
    executor.attach_barcode_manager(barcode_manager)
    window.action_callback = executor.handle_widget_executor
    executor.handle_serial_controller = window.handle_controller_serial_response
    executor.handle_barcode_manager = window.handle_barcode_manager_response

    # f) Таймер для обновления GUI
    # http_timer = QTimer()
    # http_timer.timeout.connect(window.handle_timer_event)
    # http_timer.start(5000)  # например, проверять раз в 5 секунд

    # g) Завершающие привязки: при закрытии Qt — останавливаем сервисы
    qt_app.aboutToQuit.connect(serial_manager.stop)
    qt_app.aboutToQuit.connect(barcode_manager.stop)
    # qt_app.aboutToQuit.connect(http_timer.stop)
    # Если хотите корректно остановить Uvicorn:
    qt_app.aboutToQuit.connect(uvicorn_thread.quit)
    qt_app.aboutToQuit.connect(uvicorn_thread.wait)

    # h) Показываем окно и входим в цикл
    window.show()
    sys.exit(qt_app.exec_())


if __name__ == "__main__":
    main()
