import threading
import time
import logging
import traceback
from typing import Any, Dict, List, Optional, Protocol, TypedDict
import logging
from .DiagnosticLogger import DiagnosticLogger
logger = logging.getLogger(__name__)


class ScheduledTask(Protocol):
    """
    Интерфейс планировщика задач, ожидающий метод schedule().
    """
    def schedule(self, func: Any, args: tuple, delay: float) -> None:
        ...


class RetryCommand(TypedDict):
    """
    Структура команды для повторной отправки.
    """
    id: str
    table: str
    operation: str
    data: Dict[str, Any]
    status: str
    timestamp: str
    retry_count: Optional[int]


class RetryManager:
    """
    Менеджер автоматического повторения неудачных команд синхронизации.

    Место в архитектуре:
      • Используется на клиенте рядом с CommandSender и CommandQueue.
      • Отвечает за планирование и выполнение повторных попыток доставки команд.
      • Интегрируется с Task Scheduler (Celery, APScheduler, asyncio) для отложенных вызовов.

    Зависимости:
      :param scheduler: Экземпляр планировщика задач, реализующий метод schedule(func, args, delay).
      :param queue:     CommandQueue — хранит команды и их статусы.
      :param sender:    CommandSender — умеет отправлять одиночные команды.
      :param _logger:    DiagnosticLogger — централизованное логирование.

    Логика работы:
      1. При первом сбое команда помечается как 'failed' и передаётся в schedule_retry().
      2. schedule_retry() регистрирует отложенный вызов _retry_one().
      3. _retry_one():
         a) Пытается отправить команду через sender.send_single().
         b) Если успех — mark_as_done(), снимает из повторов.
         c) Если провал — увеличивает retry_count, помечает как 'failed' и,
            если retry_count < max_retries, снова планирует через backoff*attempt.
      4. retry_failed_all() может запускаться периодически для массового рестарта всех 'failed'.
    """

    def __init__(
        self,
        scheduler,
        queue,
        sender,
        _logger: Optional[DiagnosticLogger] = None,
        max_retries: int = 5,
        base_delay: float = 60.0
    ) -> None:
        """
        :param scheduler:   Планировщик задач (Celery, APScheduler, asyncio loop-подобный).
        :param queue:       Локальная очередь команд.
        :param sender:      Класс, умеющий отправлять одиночные команды.
        :param _logger:      Логгер для диагностики повторов.
        :param max_retries: Максимум попыток повторной отправки каждой команды.
        :param base_delay:  Базовая задержка (сек) для первой повторной отправки.
        """
        self.scheduler = scheduler
        self.queue = queue
        self.sender = sender
        self.logger = _logger
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._lock = threading.Lock()

    def schedule_retry(self, cmd: RetryCommand, delay: Optional[float] = None) -> None:
        """
        Планирует повтор неудачной команды.

        :param cmd:   Словарь команды, включая поле 'retry_count'.
        :param delay: Задержка перед повтором (по умолчанию base_delay * 2^retry_count).
        """
        with self._lock:
            cmd_id = cmd["id"]
            count = cmd.get("retry_count", 0) + 1
            cmd["retry_count"] = count
            if count > self.max_retries:
                if self.logger:
                    self.logger.log_warning(
                        "Max retries exceeded, dropping command",
                        {"id": cmd_id, "retry_count": count}
                    )
                print(f'[ПОТОК][{threading.current_thread().name}][RetryManager][schedule_retry] - count: {len(self.queue.get_pending_commands() + self.queue.get_failed_commands())}')
                return

            self.queue.mark_as_failed(cmd_id)
            actual_delay = delay if delay is not None else self.base_delay * (2 ** (count - 1))
            if self.logger:
                self.logger.log_info(
                    "Scheduling retry",
                    {"id": cmd_id, "attempt": count, "delay": actual_delay}
                )
            self.scheduler.schedule(
                func=self._retry_one,
                args=(cmd,),
                delay=actual_delay
            )
            print(f'[ПОТОК][{threading.current_thread().name}][RetryManager][schedule_retry] - count: {len(self.queue.get_pending_commands() + self.queue.get_failed_commands())}')

    def _retry_one(self, cmd: RetryCommand) -> None:
        """
        Выполняет попытку повторной отправки одной команды.

        :param cmd: RetryCommand со всеми необходимыми полями.
        """
        cmd_id = cmd["id"]
        try:
            if self.logger:
                self.logger.log_debug("Retrying command", {"id": cmd_id, "attempt": cmd["retry_count"]})
            # Предполагается, что sender поддерживает send_single_command
            self.sender.send_single_command(cmd)
            self.queue.mark_as_done(cmd_id)
            if self.logger:
                self.logger.log_info("Command retry succeeded", {"id": cmd_id})
            print(f'[ПОТОК][{threading.current_thread().name}][RetryManager][_retry_one] - count: {len(self.queue.get_pending_commands() + self.queue.get_failed_commands())}')
        except Exception as ex:
            print(f'[ПОТОК][{threading.current_thread().name}][RetryManager][_retry_one][ERROR] - error: {ex} Не удалось повторить команду, подробности: - {traceback.format_exc()}')
            if self.logger:
                self.logger.log_error(
                    "Retry attempt failed",
                    {"id": cmd_id, "error": str(ex), "attempt": cmd["retry_count"]}
                )
            # планируем новую попытку
            self.schedule_retry(cmd)

    def retry_failed(self):
        """
        Запускает повтор для всех команд со статусом 'failed' в очереди.
        Может вызываться по расписанию (например, каждую минуту).
        """
        for cmd in self.queue.get_pending_commands() + self.queue.get_failed_commands():
            # Повторяем только те, что помечены 'failed'
            if cmd["status"] == "failed":
                self._retry_one(cmd)
        print(f'[ПОТОК][{threading.current_thread().name}][RetryManager][retry_failed] - count: {len(self.queue.get_pending_commands() + self.queue.get_failed_commands())}')


    def retry_failed_all(self) -> None:
        """
        Запускает повтор для всех команд со статусом 'failed'.
        Может вызываться по расписанию (cron, Celery beat).
        """
        failed = self.queue.get_failed_commands()
        if self.logger:
            self.logger.log_debug("Retrying all failed commands", {"count": len(failed)})
        for cmd in failed:
            # Преобразуем к RetryCommand
            rc: RetryCommand = {**cmd, "retry_count": cmd.get("retry_count", 0)}
            self.schedule_retry(rc, delay=0)
        print(f'[ПОТОК][{threading.current_thread().name}][RetryManager][retry_failed_all] - count: {len(failed)}')

# Список изменений
# Типизация через TypedDict и Protocol
# – RetryCommand описывает структуру повторяемой команды.
# – ScheduledTask задаёт интерфейс планировщика.
# DiagnosticLogger
# – Централизованное логирование всех этапов: планирование, успех, неудача, отказ после N попыток.
# Экспоненциальный backoff
# – Задержка рассчитывается как base_delay * 2^(retry_count−1), чтобы смягчить нагрузку на сеть.
# Максимум попыток (max_retries)
# – По превыщении — команда отбрасывается с предупреждением, чтобы избежать бесконечных циклов.
# Потокобезопасность
# – threading.Lock защищает инкремент счётчика и планирование.
# Методы массового и точечного повторов
# – retry_failed_all() для периодических запусков всех failed.
# – schedule_retry() для планирования конкретной команды.
# Докстринги с архитектурным контекстом
# – Описано, где и как используется RetryManager, потоки вызовов и зависимости.
# Прочая информация и рекомендации
# Метрики и мониторинг
# – Количество повторных попыток, среднее время до успеха, число отказов (drop_count).
# Асинхронный вариант
# – Можно адаптировать к asyncio и async def.
# Custom backoff
# – Реализовать стратегию “jitter” для избежания синхронизованных повторов.
# Интеграция
# – RetryManager может быть включён в единый SyncMonitor для графиков здоровья синхронизации.
# Тестирование
# – Unit-тесты на сценарии: немедленный успех, многократные сбои, drop после max_retries.
# Очистка очереди
# – При shutdown приложения можно выгрузить планировщик и остановить новые retries.
# Улучшения
# – Поддержка retry_interval на уровне таблицы/операции.
# – Endpoint для ручного запуска повторов через API администратора.