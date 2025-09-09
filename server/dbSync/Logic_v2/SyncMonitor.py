import threading
# import time
from datetime import datetime
from typing import Callable, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SyncMonitor:
    """
    Сервис сбора и экспорта метрик процесса синхронизации данных.

    Использование:
        • Интегрируется в SyncProcessor (методы process_push, prepare_pull),
          SyncManager.process_schema и другие участки логики синхронизации.
        • Фиксирует успешные и неуспешные пакеты, а также время их обработки.
        • Предоставляет API для вывода текущих метрик и регистрации внешнего экспорта.

    Метрики:
        - successful_count: int — общее число успешных операций
        - failed_count:     int — общее число проваленных операций
        - total_time:       float — суммарное время обработки (сек)
        - average_time:     float — среднее время обработки одного пакета

    Расширяемость:
        :param export_fn: Optional[Callable[[Dict[str, float]], None]]
            Функция для внешнего экспорта метрик (например, в Prometheus).
            Вызывается после каждого record_*.

    Протокол вызовов:
        monitor = SyncMonitor(export_fn=push_to_prometheus)
        start = time.time()
        try:
            ... # sync logic
            monitor.record_success(time.time() - start)
        except Exception:
            monitor.record_failure(time.time() - start)
            raise
        metrics = monitor.get_metrics()

    HTTP-эндпоинт для метрик:
        @app.get('/metrics')
        def metrics():
            return monitor.get_metrics()
    """

    def __init__(
            self,
            export_fn: Optional[Callable[[Dict[str, float]], None]] = None
    ) -> None:
        self._lock = threading.RLock()
        self._successful_count = 0
        self._failed_count = 0
        self._total_time = 0.0
        self._export_fn = export_fn
        print(f'[ПОТОК][{threading.current_thread().name}][SyncMonitor] Инициализирован. [{datetime.now()}]')

    def record_success(self, duration: float) -> None:
        """
        Зафиксировать успешно обработанный пакет.

        :param duration: время обработки в секундах.
        """
        with self._lock:
            self._successful_count += 1
            self._total_time += duration
            self._maybe_export()
        print(f'[ПОТОК][{threading.current_thread().name}][SyncMonitor] Успешно обработан пакет. [{datetime.now()}]')

    def record_failure(self, duration: float) -> None:
        """
        Зафиксировать неуспешную обработку пакета.

        :param duration: время до отказа в секундах.
        """
        with self._lock:
            self._failed_count += 1
            self._total_time += duration
            self._maybe_export()
        print(f'[ПОТОК][{threading.current_thread().name}][SyncMonitor] Неуспешная обработка пакета. [{datetime.now()}]')

    def get_metrics(self) -> Dict[str, float]:
        """
        Получить текущие агрегированные метрики.

        :return: словарь {
            'successful_count': int,
            'failed_count': int,
            'average_time': float
        }
        """
        print(f'[ПОТОК][{threading.current_thread().name}][SyncMonitor] Получены метрики. [{datetime.now()}]')
        with self._lock:
            total = self._successful_count + self._failed_count
            avg = (self._total_time / total) if total > 0 else 0.0
            return {
                'successful_count': float(self._successful_count),
                'failed_count': float(self._failed_count),
                'average_time': avg
            }

    def reset(self) -> None:
        """
        Сброс всех метрик в начальное состояние.
        """
        with self._lock:
            self._successful_count = 0
            self._failed_count = 0
            self._total_time = 0.0
            self._maybe_export()
        print(f'[ПОТОК][{threading.current_thread().name}][SyncMonitor] Метрики сброшены. [{datetime.now()}]')

    def _maybe_export(self) -> None:
        """
        Внутренний вызов функции экспорта, если она задана.
        """
        if self._export_fn:
            # Вызываем без блокировки, чтобы не держать lock долго
            metrics = self.get_metrics()
            try:
                self._export_fn(metrics)
                print(f'[ПОТОК][{threading.current_thread().name}][SyncMonitor] Метрики экспортированы. [{datetime.now()}]')
            except Exception:
                print(f'[ПОТОК][{threading.current_thread().name}][SyncMonitor] Ошибка экспорта метрик. [{datetime.now()}]')
                pass

# Ниже комментарии по обновлённому SyncMonitor:
# Полный докстринг
# – Описывает назначение в архитектуре, где и как применяется, формат метрик, примеры вызовов и экспорта.
# Функция export_fn
# – Позволяет сразу интегрировать экспорт метрик (Prometheus, StatsD, логирование) без правки логики.
# Потокобезопасность
# – Все изменения счётчиков и времени защищены threading.Lock.
# Автоматический экспорт
# – В record_success, record_failure и reset встроен вызов export_fn(metrics).
# Метод reset
# – Удобен для тестов и периодической ротации метрик.
# Типы и возвращаемые значения
# – get_metrics всегда возвращает float для совместимости с системами мониторинга.
# Рекомендации по улучшению:
# Асинхронный вариант: добавить async def-методы, если SyncProcessor асинхронен.
# Дополнительные метрики: таймеры для отдельных этапов (prepare_pull, process_push, schema).
# Исторические данные: хранить скользящее окно метрик (последние N минут).
# Метрики ошибок: классифицировать по типам исключений.
# Интеграция: использовать export_fn для прямой записи в Prometheus через Gauge.set.
