import threading
import time
import logging
import traceback
from datetime import datetime, timedelta
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
        Упрощенный метод для обновления retry_count и статуса команды.
        Больше не планирует через scheduler, используется только для обновления счетчика.

        :param cmd:   Словарь команды со статусом retrying.
        :param delay: Не используется (оставлен для совместимости).
        """
        with self._lock:
            cmd_id = cmd["id"]
            # Увеличиваем retry_count
            count = self.queue.add_retry_count(cmd_id)
            if count > self.max_retries:
                if self.logger:
                    self.logger.log_warning(
                        "Max retries exceeded, marking command as failed",
                        {"id": cmd_id, "retry_count": count}
                    )
                self.queue.mark_as_failed(cmd_id)
                logger.warning("[RetryManager][schedule_retry] Max retries exceeded for %s, marked as failed", cmd_id)
                return

            # Команда остается в статусе retrying
            if self.logger:
                self.logger.log_info(
                    "Retry count updated",
                    {"id": cmd_id, "retry_count": count}
                )
            logger.debug("[RetryManager][schedule_retry] Retry count updated for %s, count: %s", cmd_id, count)

    def _retry_one(self, cmd: RetryCommand) -> bool:
        """
        Выполняет попытку повторной отправки одной команды.

        :param cmd: RetryCommand со всеми необходимыми полями.
        :return: True если успешно, False если неудача
        """
        cmd_id = cmd["id"]
        current_retry_count = self.queue.get_retry_count(cmd_id)
        
        try:
            if self.logger:
                self.logger.log_debug("Retrying command", {"id": cmd_id, "attempt": current_retry_count})
            # Предполагается, что sender поддерживает send_single_command
            self.sender.send_single_command(cmd)
            self.queue.mark_as_done(cmd_id)
            if self.logger:
                self.logger.log_info("Command retry succeeded", {"id": cmd_id})
            logger.debug("[RetryManager][_retry_one] Command %s retry succeeded", cmd_id)
            return True
        except Exception as ex:
            logger.exception("[RetryManager][_retry_one] Не удалось повторить команду %s: %s", cmd_id, ex)
            if self.logger:
                self.logger.log_error(
                    "Retry attempt failed",
                    {"id": cmd_id, "error": str(ex), "attempt": current_retry_count}
                )
            # Обновляем timestamp последней попытки
            now_iso = datetime.utcnow().isoformat() + "Z"
            self.queue.update_last_retry_timestamp(cmd_id, now_iso)
            # Увеличиваем retry_count
            self.schedule_retry(cmd)
            return False

    def retry_failed(self):
        """
        Запускает повтор для всех команд со статусом 'failed' в очереди.
        Может вызываться по расписанию (например, каждую минуту).
        """
        for cmd in self.queue.get_pending_commands() + self.queue.get_failed_commands():
            # Повторяем только те, что помечены 'failed'
            if cmd["status"] == "failed":
                self._retry_one(cmd)
        logger.debug("[RetryManager][retry_failed] count: %s", len(self.queue.get_pending_commands() + self.queue.get_failed_commands()))


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
        logger.info("[RetryManager][retry_failed_all] count: %s", len(failed))

    def retry_all_retrying(self) -> int:
        """
        Обрабатывает все retrying команды итеративно.
        Проверяет timestamp последней попытки и обрабатывает только те команды,
        которые не обрабатывались последние base_delay секунд.

        :return: Количество успешно обработанных команд
        """
        with self._lock:
            retrying = self.queue.get_retrying_commands()
            if not retrying:
                if self.logger:
                    self.logger.log_debug("No retrying commands to process")
                return 0

            if self.logger:
                self.logger.log_info("Processing retrying commands", {"count": len(retrying)})
            logger.info("[RetryManager][retry_all_retrying] Processing %s retrying commands", len(retrying))

            now = datetime.utcnow()
            success_count = 0
            processed_count = 0

            for cmd in retrying:
                cmd_id = cmd["id"]
                retry_count = self.queue.get_retry_count(cmd_id)
                
                # Проверяем max_retries
                if retry_count >= self.max_retries:
                    if self.logger:
                        self.logger.log_warning(
                            "Max retries exceeded, marking as failed",
                            {"id": cmd_id, "retry_count": retry_count}
                        )
                    self.queue.mark_as_failed(cmd_id)
                    continue

                # Проверяем timestamp последней попытки
                last_retry_ts = self.queue.get_last_retry_timestamp(cmd_id)
                if last_retry_ts:
                    try:
                        last_retry_time = datetime.fromisoformat(last_retry_ts.replace('Z', '+00:00'))
                        time_since_last = (now - last_retry_time.replace(tzinfo=None)).total_seconds()
                        if time_since_last < self.base_delay:
                            # Еще не прошло достаточно времени с последней попытки
                            continue
                    except (ValueError, TypeError) as e:
                        # Если timestamp некорректный, обрабатываем команду
                        if self.logger:
                            self.logger.log_warning(
                                "Invalid last_retry_timestamp, processing anyway",
                                {"id": cmd_id, "error": str(e)}
                            )

                # Обновляем timestamp перед попыткой
                now_iso = datetime.utcnow().isoformat() + "Z"
                self.queue.update_last_retry_timestamp(cmd_id, now_iso)
                processed_count += 1

                # Преобразуем к RetryCommand
                rc: RetryCommand = {
                    "id": cmd_id,
                    "table": cmd["table"],
                    "operation": cmd["operation"],
                    "data": cmd["data"],
                    "status": cmd["status"],
                    "timestamp": cmd["timestamp"],
                    "retry_count": retry_count
                }

                # Пытаемся отправить команду
                if self._retry_one(rc):
                    success_count += 1

            logger.info("[RetryManager][retry_all_retrying] Processed %s commands, %s succeeded", processed_count, success_count)
            if self.logger:
                self.logger.log_info(
                    "Retry all retrying completed",
                    {"processed": processed_count, "succeeded": success_count, "total": len(retrying)}
                )
            return success_count

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
