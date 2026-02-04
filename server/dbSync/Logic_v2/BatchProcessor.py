import threading
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional, TypedDict
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .SyncManager import SyncManager
from .DiagnosticLogger import DiagnosticLogger
import logging
logger = logging.getLogger(__name__)


class Operation(TypedDict, total=False):
    """
    Описание одной операции синхронизации.
    """
    command_id: int  # ID команды из журнала синхронизации
    table: str  # целевая таблица
    operation: str  # "insert" | "update" | "delete"
    data: Dict[str, Any]  # полезная нагрузка (локальный формат)
    id: Optional[int]  # существующий PK (для update/delete)


class OperationResult(TypedDict, total=False):
    """
    Результат применения одной операции.
    """
    command_id: int
    success: bool
    new_id: Optional[int]  # для insert — созданный PK
    error: Optional[str]  # текст ошибки при неуспехе


class BatchProcessor:
    """
    Атомарная пакетная обработка CRUD-операций, полученных от SyncProcessor.

    Место в архитектуре:
      • Вызывается внутри SyncProcessor.process_push() сразу после разрешения конфликтов и мэппинга.
      • Группирует все операции в одну транзакцию SQLAlchemy.
      • Делегирует каждую операцию в SyncManager.process_command().
      • Собирает и возвращает подробный результат по каждой команде.

    Зависимости:
      :param session:       Экземпляр SQLAlchemy Session для управления транзакцией.
      :param sync_manager:  SyncManager — маршрутизатор к конкретным CRUD-классам.
      :param _logger:        DiagnosticLogger — для централизованного логирования.

    Логика:
      1. Открываем транзакцию (session.begin()).
      2. Для каждой операции:
         a) Вызываем _apply_single(op) — обёртка над sync_manager.process_command().
         b) На успех — помещаем в results запись с success=True и опциональным new_id.
         c) На неудачу — логируем, добавляем ошибку в results, и прерываем цикл (raise),
            чтобы откатить всю транзакцию.
      3. В случае отката транзакции (SQLAlchemyError) возвращаем накопленные результаты.
      4. Иначе — возвращаем полный список результатов с success=True.
    """

    def __init__(
            self,
            session: Session,
            sync_manager: SyncManager,
            _logger: Optional[DiagnosticLogger] = None
    ):
        """
        :param session:      SQLAlchemy Session для транзакций.
        :param sync_manager: Отвечает за выбор нужного CRUD-класса и метод apply.
        :param _logger:       (Опционально) DiagnosticLogger для логирования.
        """
        self.session = session
        self.sync_manager = sync_manager
        # Если внешний DiagnosticLogger не передан, используем стандартный logging
        self.logger = _logger or logging.getLogger(__name__)

    def execute_batch(self, operations: List[Operation]) -> List[OperationResult]:
        """
        Применяет список операций в одной транзакции и возвращает результат по каждой.

        :param operations: Список Operation:
            {
              "command_id": int,
              "table": str,
              "operation": str,
              "data": dict,
              "id": Optional[int]
            }
        :return: Список OperationResult:
            {
              "command_id": int,
              "success": bool,
              "new_id": Optional[int],
              "error": Optional[str]
            }
        """
        # Предварительная обработка: связываем Consumption с History из текущего батча
        self._link_consumption_to_history(operations)
        
        results: List[OperationResult] = []
        try:
            with self.session.begin_nested():
                for op in operations:
                    try:
                        res = self._apply_single(op)
                        new_id = None
                        if isinstance(res, dict):
                            # INSERT вернёт {'id': ...}, UPDATE/DELETE — {} → safe get
                            new_id = res.get('id', None)
                        else:
                            new_id = getattr(res, 'id', None)

                        results.append({
                            "command_id": op["command_id"],
                            "success": True,
                            "new_id": new_id
                        })
                        print(f'[ПОТОК][{threading.current_thread().name}][BatchProcessor][execute_batch][INFO] - command_id: {op["command_id"]}. [{datetime.now()}]')
                    except Exception as e:
                        print(f'[ПОТОК][{threading.current_thread().name}][BatchProcessor][execute_batch][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
                        # Логируем подробности ошибки
                        if self.logger:
                            self.logger.log_error(
                                f"BatchProcessor failed on command {op['command_id']}",
                                {"operation": op, "exception": str(e)}
                            )
                        results.append({
                            "command_id": op["command_id"],
                            "success": False,
                            "error": str(e)
                        })
                        # Останавливаем пакет — откат всей транзакции
                        raise
        except SQLAlchemyError as e:
            print(f'[ПОТОК][{threading.current_thread().name}][BatchProcessor][execute_batch][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
            # Транзакция откатилась — возвращаем накопленные результаты
            return results

        return results

    def _apply_single(self, op: Operation) -> Dict[str, Any]:
        """
        Обёртка для SyncManager.process_sync_command() for sync operations.
        Позволяет обработать возвращаемое значение (например, новый PK при insert).

        :param op: Operation
        :return: Словарь с дополнительными данными, например {"new_id": int}
        :raises: Любые ошибки от sync_manager для отката транзакции.
        """
        payload = {
            "table": op["table"],
            "operation": op["operation"].lower(),  # нормируем регистр
            "data": op["data"]
        }
        if op.get("id") is not None:
            payload["id"] = op["id"]
        import dbSync
        # Отладочное логирование: поддерживаем и DiagnosticLogger, и обычный logging.Logger
        if isinstance(self.logger, DiagnosticLogger):
            self.logger.log_debug(
                "[BatchProcessor] _apply_single start",
                {
                    "command_id": op.get("command_id"),
                    "table": op.get("table"),
                    "operation": op.get("operation"),
                },
            )
        else:
            self.logger.debug(
                "[BatchProcessor] _apply_single start: command_id=%s, table=%s, operation=%s",
                op.get("command_id"),
                op.get("table"),
                op.get("operation"),
            )
        try:
            dbSync.init_db = True
            # Use process_sync_command with sync_context=True for sync operations
            result = self.sync_manager.process_sync_command(
                payload, sync_context=True
            )
            if isinstance(self.logger, DiagnosticLogger):
                self.logger.log_debug(
                    "[BatchProcessor] _apply_single success",
                    {"command_id": op.get("command_id")},
                )
            else:
                self.logger.debug(
                    "[BatchProcessor] _apply_single success: command_id=%s",
                    op.get("command_id"),
                )
        except Exception as e:
            # Логируем и гарантированно сбрасываем флаг init_db
            if isinstance(self.logger, DiagnosticLogger):
                self.logger.log_exception(
                    e,
                    {
                        "stage": "_apply_single",
                        "command_id": op.get("command_id"),
                    },
                )
            else:
                self.logger.exception(
                    "[BatchProcessor] _apply_single error for command_id=%s; resetting dbSync.init_db to False",
                    op.get("command_id"),
                )
            raise
        finally:
            if getattr(dbSync, "init_db", False):
                if isinstance(self.logger, DiagnosticLogger):
                    self.logger.log_debug(
                        "[BatchProcessor] _apply_single: resetting dbSync.init_db from True to False",
                        {"command_id": op.get("command_id")},
                    )
                else:
                    self.logger.debug(
                        "[BatchProcessor] _apply_single: resetting dbSync.init_db from True to False"
                    )
                dbSync.init_db = False

        # Ожидаем, что process_sync_command вернёт new_id для insert
        return result or {}
    
    def _link_consumption_to_history(self, operations: List[Operation]) -> None:
        """
        Предварительная обработка: связывает Consumption с History из текущего батча команд.
        Если Consumption не имеет history_id, ищет связанную History в том же батче.
        """
        # Собираем все History команды из батча
        history_commands = {}
        for op in operations:
            if op.get("table") == "History" and op.get("operation", "").lower() in ("add", "insert"):
                history_id = op.get("data", {}).get("id") or op.get("data", {}).get("index")
                tools_id = op.get("data", {}).get("tools_id")
                if history_id and tools_id:
                    if tools_id not in history_commands:
                        history_commands[tools_id] = []
                    history_commands[tools_id].append((history_id, op))
        
        # Обновляем Consumption команды, добавляя history_id
        for op in operations:
            if op.get("table") == "Consumption" and op.get("operation", "").lower() in ("add", "insert"):
                data = op.get("data", {})
                if "history_id" not in data or data.get("history_id") is None:
                    tools_id = data.get("tools_id")
                    if tools_id and tools_id in history_commands:
                        # Берём последнюю History для этого tools_id
                        history_list = history_commands[tools_id]
                        if history_list:
                            # Сортируем по timestamp или используем последнюю
                            latest_history_id = history_list[-1][0]
                            data["history_id"] = latest_history_id
                            print(f'[ПОТОК][{threading.current_thread().name}][BatchProcessor][_link_consumption_to_history] Linked Consumption to History {latest_history_id} from batch for tools_id={tools_id}')

# Список изменений в обновлённой версии класса:
#
# TypedDict для операций и результатов
# — Ввёл Operation и OperationResult для строгой типизации входных и выходных данных.
#
# DiagnosticLogger
# — Добавил необязательный логгер для централизованного логирования ошибок и контекста.
#
# Новый приватный метод _apply_single
# — Выделил логику одного вызова sync_manager.process_command() для лучшей читаемости и расширяемости (например, подмена CRUD-логики или post-processing).
#
# Обработка возвращаемого new_id
# — Если при вставке CRUD-класс возвращает ID новой записи, мы его сохраняем в результатах.
#
# Улучшенная нормализация и валидация параметров
# — Приведение команды к нижнему регистру (operation.lower()), чтобы избежать проблем с разным регистром.
#
# Расширенный докстринг
# — Полное описание места в архитектуре, зависимостей, входных/выходных данных, логики работы.
#
# Прочая важная информация и предложения по улучшению:
#
# Параллельная обработка
# Если объём операций очень большой, можно рассмотреть разбивку на несколько транзакций или фоновые воркеры для снижения блокировок БД.
#
# Пользовательские стратегии отката
# Вместо мгновенного отката всей пачки на первой же ошибке, можно собирать успешные результаты и при ошибке частично коммитить, а проблемные операции откатывать индивидуально (в зависимости от требований at-least-once vs exactly-once).
#
# Метрики и мониторинг
# Внедрить счётчики успешных/неуспешных команд, время выполнения пачки, и отправлять в Prometheus или другой APM.
#
# Улучшение читаемости
# — Вынести маппинг ключей (table, operation, data, id) в константы или конфигурацию.
# — Явно проверять на валидность operation (вместо ожидания, что SyncManager сам это сделает).
#
# Использование библиотек
# Можно рассмотреть pydantic для валидации и парсинга входящих операций вместо TypedDict. Это даст автогенерацию докстрингов и проверки типов на этапе выполнения.
#
# Документация и диаграммы
# Для полного понимания потока данных рекомендуются Sequence Diagram (например, PlantUML) для иллюстрации:
#
# rust
# Копировать
# Редактировать
# SyncProcessor -> BatchProcessor: execute_batch(operations)
# BatchProcessor -> Session: begin transaction
# BatchProcessor -> SyncManager: process_command(op1)
# SyncManager -> CRUD_Insert: insert(data)
# CRUD_Insert --> SyncManager: new_id
# BatchProcessor --> Session: commit or rollback
# Тесты
# Добавить unit-тесты на разные сценарии:
#
# Все операции успешны.
#
# Ошибка в середине пачки.
#
# Операции разных типов и таблиц.
#
# Таким образом BatchProcessor становится более надёжным, прозрачным и вписывается во всю цепочку синхронизации между SyncProcessor и CRUD-слоем.
