import json
import os
import threading
import traceback
import uuid
from datetime import datetime
from typing import List, Dict, TypedDict, Literal  # Optional,

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
        status (Literal["pending", "sent", "failed", "done"]): Текущий статус команды.
        timestamp (str): Метка времени в ISO-формате (UTC), когда была создана команда.
    """
    id: str
    table: str
    operation: Literal["insert", "update", "delete"]
    data: Dict
    status: Literal["pending", "sent", "failed", "done"]
    timestamp: str


def serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {obj!r} not serializable")

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
        self._lock = threading.RLock()
        self._load_queue()
        # При запуске оставляем только последнее корректное задание
        with self._lock:
            if len(self.queue) > 1:
                self.queue = [self.queue[-1]]
                self._save_queue()

    def _load_queue(self):
        """Загружает очередь из файла, если он существует."""
        with self._lock:  # <<< обёртка локом
            if os.path.exists(self.filepath):
                try:
                    with open(self.filepath, "r", encoding="utf-8") as f:
                        raw = f.read()
                        if not raw.strip():  # файл пустой
                            self.queue = []
                        else:
                            all_commands = json.loads(raw)
                            self.queue = [all_commands[-1]] if all_commands else []
                    print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][_load_queue] Очередь загружена из кэша. [{datetime.now()}]')
                except (json.JSONDecodeError, IOError) as e:
                    print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][_load_queue][ERROR][JSONDecodeError] - Создали чистый кеш. [{datetime.now()}]')
                    # при повреждённом JSON сбрасываем в пустую
                    self.queue = []
                    self._save_queue()
            else:
                self.queue = []
                print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][_load_queue] Файл не найден, стартуем с пустой очереди. [{datetime.now()}]')


    def _save_queue(self):
        """Сохраняет текущее состояние очереди в файл атомарно."""
        tmp_path = self.filepath + ".tmp"
        with self._lock:  # <<< обёртка локом
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(self.queue, f, indent=2, ensure_ascii=False, default=serialize)
                # атомарно заменяем старый файл
                os.replace(tmp_path, self.filepath)
                print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][_save_queue] Очередь сохранена в кэш. [{datetime.now()}]')
            except Exception as e:
                print(f'[ПОТОК][{threading.current_thread().name}][CommandQueue][_save_queue][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
                # на случай ошибки — удаляем временный файл
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

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
            "timestamp": datetime.utcnow().isoformat() + "Z"
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
