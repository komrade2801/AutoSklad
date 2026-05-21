import json
import sys
import traceback
import ast
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Tuple
import os
import logging

import uvicorn
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from fastapi import FastAPI

from BarcodeScanner.serial_manager import SerialManager
from BarcodeScanner.MockSerialManager import MockSerialManager
from BarcodeScanner.vending_serial_manager import VendingSerialManager
from BarcodeScanner.MockVendingSerialManager import MockVendingSerialManager
from BarcodeScanner.dispense_command_gate import DispenseCommandGate
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


def _hal_default_is_long(command: str) -> bool:
    c = (command or "").strip()
    if c.startswith("$"):
        c = c[1:].strip()
    u = c.upper()
    if u.startswith("LOCK,") or u.startswith("SOL,"):
        return True
    return u == "ZERO" or u.startswith("MOT,") or (c.upper().startswith("MOT") and "," in c)


def load_hal_test_scenario_steps(scenario_path: Path) -> List[Tuple[str, bool]]:
    payload = json.loads(scenario_path.read_text(encoding="utf-8"))
    raw_steps = payload.get("steps") or []
    out: List[Tuple[str, bool]] = []
    for entry in raw_steps:
        if not isinstance(entry, dict):
            continue
        cmd = (entry.get("command") or "").strip()
        if not cmd:
            continue
        if "is_long" in entry and entry["is_long"] is not None:
            is_long = bool(entry["is_long"])
        else:
            is_long = _hal_default_is_long(cmd)
        out.append((cmd, is_long))
    return out


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
        hw_cfg = cfg.get("hardware") or {}
        controller_protocol = (hw_cfg.get("protocol") or "legacy").strip().lower()
        hal_baud = int(hw_cfg.get("baudrate") or cfg.get("serial", {}).get("baudrate") or 9600)
        logger.info(
            "Platform: %s, Mock mode: %s, controller protocol: %s",
            current_platform,
            use_mocks,
            controller_protocol,
        )

        if use_mocks:
            if controller_protocol == "atmega_hal":
                serial_manager = MockVendingSerialManager(
                    port=None,
                    baudrate=hal_baud,
                    bridge_ok_to_fsm=False,
                    bridge_done_to_fsm=False,
                    bridge_error_to_fsm=False,
                    emulate_no_block_plata=True,
                )
                logger.info("Using MockVendingSerialManager (atmega HAL)")
            else:
                serial_manager = MockSerialManager(port=None)
                logger.info("Using MockSerialManager (legacy cell number)")
            barcode_manager = MockSerialManager(port=None)
            logger.info("Barcode: mock serial manager")
        else:
            if controller_protocol == "atmega_hal":
                if current_platform == platforms.Windows:
                    ctrl_port = cfg["serial"]["port"]
                    logger.info("Windows: HAL controller port=%s baud=%s", ctrl_port, hal_baud)
                else:
                    dev_ports = cfg.get("dev") or {}
                    ctrl_port = dev_ports.get("hal_uart") or dev_ports.get("serial") or dev_ports.get("ttyUSB")
                    logger.info("Linux/RPi: HAL controller port=%s baud=%s", ctrl_port, hal_baud)
                serial_manager = VendingSerialManager(
                    port=ctrl_port,
                    baudrate=hal_baud,
                    bridge_ok_to_fsm=False,
                    bridge_done_to_fsm=False,
                    bridge_error_to_fsm=False,
                )
            elif current_platform == platforms.Windows:
                serial = cfg["serial"]
                serial_manager = SerialManager(port=serial["port"])
                logger.info("Windows: legacy controller port=%s", serial["port"])
            else:
                ports = cfg["dev"]
                serial_manager = SerialManager(port=ports["ttyUSB"])
                logger.info("Linux/RPi: legacy controller port=%s", ports["ttyUSB"])

            barcode_cfg = cfg.get("barcode") or {}
            bc_baud = int(barcode_cfg.get("baudrate") or 9600)
            if current_platform == platforms.Windows:
                bc_port = barcode_cfg.get("port") or "COM1"
                barcode_manager = SerialManager(port=bc_port, baudrate=bc_baud)
                logger.info("Windows: Barcode port=%s baud=%s", bc_port, bc_baud)
            else:
                ports = cfg.get("dev") or {}
                # Linux: Windows/моки не трогаем. На Raspberry сканер по GPIO — /dev/serial1,
                # если в dev не заданы barcode_uart / barcode_serial (не откатываемся на dev.serial = HAL).
                if current_platform == platforms.Raspberry_Pi:
                    bc_port = (
                        ports.get("barcode_uart")
                        or ports.get("barcode_serial")
                        or "/dev/serial1"
                    )
                else:
                    bc_port = (
                        ports.get("barcode_uart")
                        or ports.get("barcode_serial")
                        or ports.get("serial")
                    )
                barcode_manager = SerialManager(port=bc_port, baudrate=bc_baud)
                logger.info(
                    "Linux: Barcode port=%s baud=%s (RPi=%s)",
                    bc_port,
                    bc_baud,
                    current_platform == platforms.Raspberry_Pi,
                )

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
        # Стартуем с cmd_start: проверка готовности железа (HAL контракт) до допуска в UI.
        maps = Maps('cmd_start')
        window = MainWindow(maps, controller_protocol=controller_protocol)
        executor = Executor()
        executor.controller_protocol = controller_protocol
        executor.attach_serial_manager(serial_manager)
        executor.attach_barcode_manager(barcode_manager)
        window.action_callback = executor.handle_widget_executor
        window.executor = executor
        executor.handle_serial_controller = window.handle_controller_serial_response
        executor.handle_barcode_manager = window.handle_barcode_manager_response
        # Повторно инициируем текущее стартовое состояние после подключения action_callback,
        # иначе cmd_start может остаться "немым" (открыт до подключения executor).
        window.open_widget(window.lump.state(), None, None)
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

        scenario_rel = (cfg.get("hal_test_scenario_path") or "").strip()
        hal_test_autorun = bool(cfg.get("hal_test_autorun", False)) or (os.getenv("AUTOSKLAD_HAL_TEST_AUTORUN", "0") == "1")
        if scenario_rel and controller_protocol == "atmega_hal" and hal_test_autorun:
            scenario_path = Path(scenario_rel)
            if not scenario_path.is_absolute():
                scenario_path = Path(__file__).resolve().parent / scenario_path
            if not scenario_path.is_file():
                logger.warning("HAL test: файл сценария не найден: %s", scenario_path)
            else:
                try:
                    hal_steps = load_hal_test_scenario_steps(scenario_path)
                except Exception as exc:
                    logger.error(
                        "HAL test: не удалось прочитать сценарий %s: %s",
                        scenario_path,
                        exc,
                        exc_info=True,
                    )
                    hal_steps = []

                if hal_steps:
                    hal_gate = DispenseCommandGate(serial_manager, parent=window)

                    def _hal_step_started(idx: int, cmd: str) -> None:
                        logger.info("[HAL test] шаг %s: отправка %r", idx, cmd)

                    def _hal_step_completed(idx: int, cmd: str, outcome: str) -> None:
                        logger.info(
                            "[HAL test] шаг %s: завершено %r исход=%s",
                            idx,
                            cmd,
                            outcome,
                        )

                    def _hal_sequence_finished() -> None:
                        logger.info("[HAL test] цепочка успешно завершена (%s шагов)", len(hal_steps))

                    def _hal_sequence_failed(idx: int, cmd: str, reason: str) -> None:
                        logger.error(
                            "[HAL test] сбой на шаге %s cmd=%r: %s",
                            idx,
                            cmd,
                            reason,
                        )

                    def _hal_sequence_aborted() -> None:
                        logger.warning("[HAL test] цепочка прервана (abort)")

                    def _hal_raw_line(line: str) -> None:
                        logger.debug("[HAL test] RX: %s", line)

                    hal_gate.step_started.connect(_hal_step_started)
                    hal_gate.step_completed.connect(_hal_step_completed)
                    hal_gate.sequence_finished.connect(_hal_sequence_finished)
                    hal_gate.sequence_failed.connect(_hal_sequence_failed)
                    hal_gate.sequence_aborted.connect(_hal_sequence_aborted)
                    serial_manager.raw_line.connect(_hal_raw_line)

                    def _run_hal_test_scenario() -> None:
                        logger.info(
                            "[HAL test] старт через 15 с: %s (%s шагов)",
                            scenario_path,
                            len(hal_steps),
                        )
                        if not hal_gate.run_sequence(hal_steps):
                            logger.warning(
                                "[HAL test] run_sequence отклонён (уже выполняется?)",
                            )

                    QTimer.singleShot(15_000, _run_hal_test_scenario)
                else:
                    logger.warning("HAL test: в файле нет шагов: %s", scenario_path)
        elif scenario_rel and controller_protocol != "atmega_hal":
            logger.info(
                "HAL test: путь задан, но сценарий не запускается "
                "(hardware.protocol не atmega_hal)",
            )
        elif scenario_rel and controller_protocol == "atmega_hal" and not hal_test_autorun:
            logger.info(
                "HAL test: путь задан, но автостарт отключён "
                "(включите hal_test_autorun=true или AUTOSKLAD_HAL_TEST_AUTORUN=1)",
            )

        sys.exit(qt_app.exec_())
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске приложения: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
