import json
import sys
import traceback
import ast
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List
import os
import logging

import uvicorn
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from fastapi import FastAPI

from BarcodeScanner.serial_manager import SerialManager
from BarcodeScanner.MockSerialManager import MockSerialManager
from Core import platforms
from Core.sync_config import SyncConfig
from Core.app_logging import setup_app_logging, get_logger
from DB.Data.sqlite_db import SessionLocal
from EventsSystem.Executor import Executor
from GUI.MainWindow import MainWindow
from StateMachine.FMS import Maps
from StateMachine.converter_xml_2 import map_builder

from dbSync.Runner import start_sync, stop_sync
from dbSync.Transport.routers import sync_router

# Настройка логирования для всего приложения
setup_app_logging(
    log_dir="logs",
    app_log_file="app.log",
    sync_log_file="sync.log",
    error_log_file="error.log",
    level=logging.DEBUG,
    console_output=True
)
logger = get_logger(__name__)


# ------------------------------------------------------------
# 1) Определяем lifespan для FastAPI: здесь читаем config.json,
#    запускаем sync-потоки и регистрируем stop_sync на shutdown.
# ------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = SyncConfig()

    logger.info(f"SYNC CONFIG: device_id={cfg.device_id}, host={cfg.ip}, port={cfg.port}")

    start_sync(
        device_id=cfg.device_id,
        host=cfg.ip,
        port=cfg.port,
        token=cfg.token,
        secret=cfg.secret,
        aes=cfg.aes,
        scheduler_sender_timeout=cfg.sender_timeout,
        scheduler_receiver_timeout=cfg.receiver_timeout,
        push_http_timeout=cfg.push_http_timeout
    )
    logger.info("Synchronization started")
    yield
    logger.info("Stopping synchronization...")
    stop_sync(cfg.device_id)
    logger.info("Synchronization stopped")

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
# ------------------------------------------------------------


def check_and_initialize_databases():
    """Ensure both vending.db and sync.db exist with proper schemas"""
    logger.info("Checking database initialization...")

    # 1. Check vending.db
    from config import db_path
    from sqlalchemy import create_engine, inspect
    import traceback
    from pathlib import Path

    # Main DB path - use absolute path based on script location (ALWAYS client/)
    client_dir = Path(__file__).parent.resolve()  # client/ directory
    main_db_path = client_dir / "DB" / "Data" / db_path

    # Convert Path to string for compatibility
    full_main_db_path = str(main_db_path)

    needs_setup = False
    if not os.path.exists(full_main_db_path):
        logger.warning(f"Main database not found at {main_db_path}. Running initial setup...")
        needs_setup = True
    else:
        # Quick validity check
        try:
            engine = create_engine(f"sqlite:///{full_main_db_path}")
            inspector = inspect(engine)
            required_tables = ['User', 'Cell', 'Tools', 'Role']  # Core tables
            existing = inspector.get_table_names()
            missing_tables = [
                table for table in required_tables if table not in existing]
            if missing_tables:
                logger.warning(f"Main database schema incomplete. Missing tables: {missing_tables}. Rebuilding...")
                engine.dispose()
                needs_setup = True
            else:
                engine.dispose()
                logger.info("Main database is valid.")
        except Exception as e:
            logger.error(f"Main database corrupted: {e}. Rebuilding...", exc_info=True)
            # Cleanup potentially locked connections
            try:
                if 'engine' in locals():
                    engine.dispose()
            except:
                pass
            needs_setup = True

    if needs_setup:
        try:
            run_database_setup()
        except Exception as setup_error:
            logger.critical(f"Fatal: Database setup failed: {setup_error}", exc_info=True)
            logger.critical("Cannot continue without proper database. Please check permissions and try again.")
            sys.exit(1)

    # 2. Check sync.db (will be auto-created by sync components if needed)
    logger.info("Database initialization complete.")


def run_database_setup():
    """Run the database setup process as in Create_db.py"""
    import dbSync
    dbSync.set_skip_sync_enqueue(True)
    try:
        from DB.Create_db import clear_command_queue_cache, rebuild_db, execute

        logger.info("Rebuilding main database structure...")
        clear_command_queue_cache()
        rebuild_db()  # Recreates vending.db structure
        logger.info("Populating database with initial data...")
        execute()     # Populates with test data/roles/users
        logger.info("Database setup completed successfully.")
    except Exception as e:
        logger.error(f"Database setup failed: {e}", exc_info=True)
        raise RuntimeError(f"Database setup failed: {e}") from e
    finally:
        dbSync.set_skip_sync_enqueue(False)


# 4) Точка входа для GUI-приложения
# ------------------------------------------------------------
def main():
    logger.info("=" * 60)
    logger.info("Запуск клиентского приложения AutoSklad...")
    logger.info("=" * 60)
    
    try:
        # a) Проверяем и инициализируем базы данных ПЕРВЫМИ
        check_and_initialize_databases()

        # b) Билдим карты — подготовка FSM
        # e) Запускаем Uvicorn в фоне
        #    Бери host/port из config.json, как в lifespan
        cfg = json.loads(
            (Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
        # Карта состояний берётся из state_map.py. Регенерация из screen.mm отключена,
        # чтобы не затирать правки в state_map.py. Чтобы пересобрать из .mm вручную:
        #   python -m StateMachine.converter_xml_2
        # logger.info("Building state machine maps...")
        # map_builder()
        # logger.info("State machine maps built successfully")

        # b) Запускаем Qt-приложение
        logger.info("Initializing Qt application...")
        qt_app = QApplication(sys.argv)

        # c) Настраиваем SerialManager/BarcodeManager
        use_mocks = os.getenv("AUTOSKLAD_USE_MOCKS", "0") == "1"
        current_platform = platforms.detect()
        logger.info(f"Platform: {current_platform}, Mock mode: {use_mocks}")
        
        if use_mocks:
            serial_manager = MockSerialManager(port=None)
            barcode_manager = MockSerialManager(port=None)
            logger.info("Using mock serial managers")
        else:
            if current_platform == platforms.Windows:
                serial = cfg["serial"]
                serial_manager = SerialManager(port=serial["port"])
                barcode = cfg["barcode"]
                barcode_manager = SerialManager(port=barcode["port"])
                logger.info(f"Windows: Serial port={serial['port']}, Barcode port={barcode['port']}")
            else:  # Raspberry Pi и др.
                ports = cfg["dev"]
                serial_manager = SerialManager(port=ports["ttyUSB"])
                barcode_manager = SerialManager(port=ports["serial"])
                logger.info(f"Linux/RPi: Serial port={ports['ttyUSB']}, Barcode port={ports['serial']}")

        serial_manager.start()
        barcode_manager.start()
        logger.info("Serial managers started")

        opts = cfg["network"]
        host_ip = opts["ip"]
        port = int(opts["port"])

        uvicorn_thread = UvicornThread(ip=host_ip, port=port)
        uvicorn_thread.setObjectName("UvicornThread")
        uvicorn_thread.start()
        logger.info(f"Uvicorn server started on {host_ip}:{port}")

        # e) Основная логика GUI
        logger.info("Initializing GUI components...")
        maps = Maps('screen_1_welcome')
        window = MainWindow(maps)
        executor = Executor()
        executor.attach_serial_manager(serial_manager)
        executor.attach_barcode_manager(barcode_manager)
        window.action_callback = executor.handle_widget_executor
        executor.handle_serial_controller = window.handle_controller_serial_response
        executor.handle_barcode_manager = window.handle_barcode_manager_response
        logger.info("GUI components initialized")

        # f) Таймер для обновления GUI
        # http_timer = QTimer()
        # http_timer.timeout.connect(window.handle_timer_event)
        # http_timer.start(5000)  # например, проверять раз в 5 секунд

        # g) Завершающие привязки: при закрытии Qt — останавливаем сервисы
        def cleanup():
            logger.info("Application shutdown initiated...")
            serial_manager.stop()
            barcode_manager.stop()
            logger.info("Serial managers stopped")
        
        qt_app.aboutToQuit.connect(cleanup)
        # qt_app.aboutToQuit.connect(http_timer.stop)
        # Если хотите корректно остановить Uvicorn:
        qt_app.aboutToQuit.connect(uvicorn_thread.quit)
        qt_app.aboutToQuit.connect(uvicorn_thread.wait)

        # h) Показываем окно и входим в цикл
        logger.info("=" * 60)
        logger.info("Клиентское приложение готово к работе")
        logger.info("=" * 60)
        window.show()
        sys.exit(qt_app.exec_())
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске приложения: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
