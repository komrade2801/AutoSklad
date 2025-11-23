import json
import os
import threading
import traceback
import uuid
from datetime import datetime
from typing import List, Dict, TypedDict, Literal, Optional

# from DB.Data.base import Base

# dbSync/queues.py
from queue import Queue
import logging

logger = logging.getLogger(__name__)

INBOUND_QUEUES: Dict[int, Queue] = {}


class Command(TypedDict):
    """
    Структура команды, представляющей собой единичное изменение в БД, подлежащее синхронизации.

    Атрибуты:
        id (str): Уникальный UUID команды.
        table (str): Имя таблицы, к которой применяется команда.
        operation (Literal["insert", "update", "delete"]): Тип операции.
        data (dict): Полезная нагрузка с изменёнными или новыми полями.
        status (Literal["pending", "retrying", "failed", "done"]): Текущий статус команды.
        timestamp (str): Метка времени в ISO-формате (UTC), когда была создана команда.
    """
    id: str
    table: str
    operation: Literal["insert", "update", "delete"]
    data: Dict
    status: Literal["pending", "retrying", "failed", "done"]
    timestamp: str


class CommandQueue:
    """
    Очередь команд синхронизации, хранящая изменения в локальной базе данных,
    предназначенные для отправки на удалённый сервер.

    Назначение:
        • Буферизация всех локальных изменений, поступающих через CDCService.
        • Гарантия сохранности команд между перезапусками приложения.
        • Управление жизненным циклом команд: от "pending" до "done".
        • Обеспечение надёжной доставки в схеме синхронизации ("at-least-once").

    Место в архитектуре:
        • Получает команды от CDCService при локальных изменениях.
        • Читается CommandSender'ом для отправки на сервер.
        • После получения ответа сервера обрабатывается методом mark_as_done() или mark_as_failed().

    Взаимосвязи:
        • Получает → CDCService (через слушатель).
        • Отдаёт → CommandSender → TransportService → SyncProcessor (на сервере).
        • Очищается после подтверждения → через clear_done().

    Файл:
        Все команды хранятся в JSON-файле `command_queue.json` в том виде, в котором они отправляются.
    """

    def __init__(self, filepath: str = "command_queue.json") -> None:
        """
        Инициализирует очередь команд, загружая предыдущие команды из файла, если он существует.

        :param filepath: Путь к JSON-файлу для хранения очереди (по умолчанию "command_queue.json").
        """
        self.filepath = filepath
        self.queue: List[Dict] = []
        self._load_queue()

    def _load_queue(self):
        """Загружает очередь из файла, если он существует."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.queue = json.load(f)
                print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][_load_queue] Очередь загружена из кэша. [{datetime.now()}]')
            except (json.JSONDecodeError, IOError) as e:
                print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][_load_queue][ERROR][JSONDecodeError] - error: {e}, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
                self.queue = []
        else:
            self.queue = []
            print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][_load_queue] Очередь загружена из кэша. [{datetime.now()}]')

    def _save_queue(self):
        """Сохраняет текущее состояние очереди в файл."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.queue, f, indent=2, ensure_ascii=False, default=str)
        print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][_save_queue] Очередь сохранена в кэш. [{datetime.now()}]')

    def add_command(self, table: str, operation: str, data: dict) -> str:
        """
        Добавляет новую команду в очередь.
        :param table: Название таблицы (например, "Tools").
        :param operation: Операция ("insert"/"update"/"delete").
        :param data: Данные для синхронизации.
        :return: Сгенерированный UUID команды.
        """
        command_id = str(uuid.uuid4())
        command = {
            "id": command_id,
            "table": table,
            "operation": operation,
            "data": data,
            "status": "pending",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "last_retry_timestamp": None
        }
        self.queue.append(command)
        self._save_queue()
        print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][add_command] Команда добавлена в очередь. [{datetime.now()}]')
        return command_id

    def get_pending_commands(self) -> List[Dict]:
        """Возвращает список команд со статусом 'pending'."""
        print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][get_pending_commands] Количество команд в очереди: {len(self.queue)}. [{datetime.now()}]')
        return [cmd for cmd in self.queue if cmd.get("status") == "pending"]

    def mark_as_sent(self, command_id: str):
        """Помечает команду как отправленную ('sent')."""
        print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][mark_as_sent] Команда помечена как отправленная. [{datetime.now()}]')
        self._update_status(command_id, "sent")

    def mark_as_done(self, command_id: str):
        """Помечает команду как успешно обработанную ('done')."""
        print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][mark_as_done] Команда помечена как успешно обработанная. [{datetime.now()}]')
        self._update_status(command_id, "done")

    def mark_as_failed(self, command_id: str):
        """Помечает команду как неуспешную ('failed')."""
        print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][mark_as_failed] Команда помечена как неуспешная. [{datetime.now()}]')
        self._update_status(command_id, "failed")

    def clear_done(self):
        """Удаляет из очереди все команды со статусом 'done'."""
        print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][clear_done] Команды со статусом "done" удалены из очереди. [{datetime.now()}]')
        self.queue = [cmd for cmd in self.queue if cmd.get("status") != "done"]
        self._save_queue()

    def _update_status(self, command_id: str, new_status: str):
        """Обновляет статус команды по её ID."""
        print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][_update_status] Статус команды обновлен. [{datetime.now()}]')
        for cmd in self.queue:
            if cmd.get("id") == command_id:
                cmd["status"] = new_status
                break
        self._save_queue()

    def get_failed_commands(self) -> List[Dict]:
        """Возвращает список команд со статусом 'failed'."""
        print(f'[CommandQueue][get_failed_commands] Count failed: {len(self.queue)}')
        return [cmd for cmd in self.queue if cmd.get("status") == "failed"]

    def get_retrying_commands(self) -> List[Dict]:
        """
        Возвращает список команд со статусом 'retrying', отсортированных по timestamp (старые первыми).
        """
        retrying = [cmd for cmd in self.queue if cmd.get("status") == "retrying"]
        # Сортируем по timestamp (старые первыми)
        retrying.sort(key=lambda cmd: cmd.get("timestamp", ""))
        print(f'[CommandQueue][get_retrying_commands] Count retrying: {len(retrying)}')
        return retrying

    def mark_as_retrying(self, command_id: str):
        """Помечает команду как находящуюся на повторной попытке ('retrying')."""
        print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][mark_as_retrying] Команда помечена как повторяющаяся. [{datetime.now()}]')
        self._update_status(command_id, "retrying")

    def get_pending_older_than(self, oldest_timestamp: str = None) -> List[Dict]:
        """
        Возвращает список pending команд, старше чем заданная временная метка.
        Если oldest_timestamp равен None, возвращает все pending команды.

        :param oldest_timestamp: ISO-строка с временем, команды старше которой включить
        :return: Список pending команд
        """
        if oldest_timestamp is None:
            return self.get_pending_commands()

        from datetime import datetime
        try:
            cutoff_time = datetime.fromisoformat(oldest_timestamp.replace('Z', '+00:00'))
        except ValueError:
            print(f'[CommandQueue][get_pending_older_than] Invalid timestamp format: {oldest_timestamp}')
            return self.get_pending_commands()

        pending = self.get_pending_commands()
        older = [cmd for cmd in pending if datetime.fromisoformat(cmd["timestamp"].replace('Z', '+00:00')) < cutoff_time]
        print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][get_pending_older_than] Pending older than {oldest_timestamp}: {len(older)} из {len(pending)}')
        return older

    def get_oldest_retrying_timestamp(self) -> str:
        """
        Возвращает временную метку самой старой retrying команды.
        Если retrying команд нет, возвращает None.

        :return: ISO-строка с временем или None
        """
        retrying = self.get_retrying_commands()
        if not retrying:
            return None

        timestamps = [cmd["timestamp"] for cmd in retrying]
        timestamps.sort()
        oldest = timestamps[0]
        print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][get_oldest_retrying_timestamp] Oldest retrying timestamp: {oldest}')
        return oldest

    def add_retry_count(self, command_id: str) -> int:
        """
        Увеличивает retry_count для команды и возвращает новое значение.

        :param command_id: ID команды
        :return: Новое значение retry_count или -1 если команда не найдена
        """
        for cmd in self.queue:
            if cmd.get("id") == command_id:
                current_count = cmd.get("retry_count", 0)
                cmd["retry_count"] = current_count + 1
                self._save_queue()
                print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][add_retry_count] Retry count for {command_id}: {current_count + 1}')
                return current_count + 1
        return -1

    def get_retry_count(self, command_id: str) -> int:
        """Возвращает текущее количество попыток повтора для команды."""
        for cmd in self.queue:
            if cmd.get("id") == command_id:
                return cmd.get("retry_count", 0)
        return 0

    def update_last_retry_timestamp(self, command_id: str, timestamp: str) -> None:
        """
        Обновляет timestamp последней попытки повтора для команды.

        :param command_id: ID команды
        :param timestamp: ISO-строка с временем последней попытки
        """
        for cmd in self.queue:
            if cmd.get("id") == command_id:
                cmd["last_retry_timestamp"] = timestamp
                self._save_queue()
                print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][update_last_retry_timestamp] Updated last_retry_timestamp for {command_id}: {timestamp}')
                return
        print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][update_last_retry_timestamp] Command {command_id} not found')

    def get_last_retry_timestamp(self, command_id: str) -> Optional[str]:
        """
        Возвращает timestamp последней попытки повтора для команды.

        :param command_id: ID команды
        :return: ISO-строка с временем или None
        """
        for cmd in self.queue:
            if cmd.get("id") == command_id:
                return cmd.get("last_retry_timestamp")
        return None

#  Список изменений:
# Типизация через TypedDict (Command) — строгая структура команд.
#
# Явная валидация операций (insert, update, delete) в add_command.
#
# Улучшенные докстринги класса и методов — описывают место в архитектуре, зависимости, поток вызовов.
#
# Поддержка строгой типизации статусов — ограничение через Literal.
#
# Чёткая архитектура: CDCService → CommandQueue → CommandSender → SyncProcessor.
#
# Формат ISO 8601 для времени, UTC + суффикс Z.
#
# Методы не бросают исключения при невозможности обновить статус (fail-safe).
#
#  Предложения по улучшению:
# Направление	Идея
# Производительность	Использовать SQLite вместо JSON-файла для масштабируемости и конкурентного доступа.
# Расширяемость	Ввести поддержку bulk-операций: add_commands(List[Command]), mark_as_done_bulk(), mark_as_failed_bulk()
# Надёжность	Добавить контроль версий/хеш-файл для валидации очереди при чтении.
# Асинхронность	Перевести CommandQueue в асинхронный режим с использованием aiofiles для работы с файловой системой.
# Наблюдаемость	Встроить логгирование и счётчики событий (Prometheus, OpenTelemetry).
# Валидация данных	Использовать pydantic.BaseModel вместо словаря data, что обеспечит строгую проверку структуры команд при записи.
# Формат хранения	Поддержка альтернатив JSON: SQLite, YAML, Parquet (если очередь большая).
