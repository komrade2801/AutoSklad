import logging
from typing import Optional, Dict, Any

# Примечание: Логирование настраивается централизованно через Core.app_logging.setup_app_logging()
# Этот модуль использует уже настроенную систему логирования Python


class DiagnosticLogger:
    """
    Централизованный сервис для логирования событий синхронизации.

    Отвечает за:
      - Логирование ошибок, предупреждений, информационных и отладочных сообщений;
      - Сбор контекста (stage, данные команды, трассировки) для быстрого анализа;
      - Отправку метрик (через log_metric) о ключевых показателях процесса.

    Место в архитектуре:
      • Используется в SyncProcessor, CommandSender, CommandReceiver и других классах логического слоя;
      • Передаётся в конструктор компонентов, обеспечивая единый канал логирования;
      • Не зависит от конкретного фреймворка, лишь от стандартного модуля logging.

    Протокол вызовов:
      logger = DiagnosticLogger(log_to_file=True, logfile="sync.log", level=logging.INFO)
      ...
      try:
          ...
      except Exception as e:
          logger.log_exception(e, context={"stage":"process_push","command":cmd})

      logger.log_info("Handshake completed", extras={"stage":"prepare_pull", "count":10})
      logger.log_warning("Unexpected field", extras={"field":"foo"})
      logger.log_metric("commands_processed", 5, tags={"device":device_id})
    """

    def __init__(
        self,
        log_to_file: bool = False,
        logfile: str = "sync.log",
        level: int = logging.DEBUG,
        logger_name: str = "SyncLogger"
    ) -> None:
        """
        :param log_to_file: игнорируется - логирование настроено централизованно
        :param logfile: игнорируется - логирование настроено централизованно
        :param level: уровень логирования (DEBUG, INFO и т.д.).
        :param logger_name: имя логгера.
        """
        # Используем уже настроенную систему логирования
        # Логирование настроено централизованно через Core.app_logging.setup_app_logging()
        # поэтому просто получаем логгер и устанавливаем уровень
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(level)
        
        # Не добавляем собственные handlers - используем централизованную систему
        # Это предотвращает дублирование логов

    def log_error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Логирование ошибки уровня ERROR.

        :param message: краткое описание ошибки.
        :param context: дополнительный контекст (stage, данные).
        """
        text = message + (f" | context={context}" if context else "")
        self.logger.error(text)

    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Логирование предупреждения уровня WARNING.

        :param message: описание предупреждения.
        :param context: дополнительный контекст.
        """
        text = message + (f" | context={context}" if context else "")
        self.logger.warning(text)

    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Логирование информационного сообщения.

        :param message: описание события.
        :param context: дополнительный контекст.
        """
        text = message + (f" | context={context}" if context else "")
        self.logger.info(text)

    def log_debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Логирование детальной отладки.

        :param message: описание.
        :param context: дополнительный контекст.
        """
        text = message + (f" | context={context}" if context else "")
        self.logger.debug(text)

    def log_exception(self, exc: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Логирование исключения с трассировкой.

        :param exc: 捕获нное исключение.
        :param context: дополнительный контекст.
        """
        self.logger.info(f"EXCEPTION: {exc} | context={context}", exc_info=True)

    def log_metric(self, name: str, value: Any, tags: Optional[Dict[str, Any]] = None) -> None:
        """
        Логирование метрики синхронизации.

        :param name: имя метрики.
        :param value: значение метрики.
        :param tags: дополнительные теги для метрики.
        """
        # В простейшем виде выводим в лог, интеграция с APM возможна через handler
        text = f"METRIC: {name}={value}" + (f" | tags={tags}" if tags else "")
        self.logger.info(text)


#  Список изменений в DiagnosticLogger
# Добавлены методы
# log_warning для предупреждений.
# log_exception для автоматической загрузки стектрейса.
# log_metric для учёта ключевых показателей (интеграция с APM/Prometheus).
# Унифицированные сигнатуры
# Все методы принимают необязательный context: Dict[str, Any], который дописывается к сообщению.
# Параметризация конструктора
# Параметр level позволяет задать уровень логирования.
# Параметр logger_name — для разделения логов по подсистемам.
# Структурированное сообщение
# Формат message | context={...} упрощает парсинг логов сторонними инструментами.
# Расширенный докстринг
# Полное описание задач, места в архитектуре, примеров использования и протокола вызовов.
#  Прочая важная информация
# Интеграция с внешними системами
# log_metric можно перенаправить в StatsD/Prometheus через кастомный handler.
# JSON-formatter: для централизованного хранения логов в ELK/Graylog можно заменить форматтер.
# Дополнительные уровни
# Можно добавить log_critical и log_trace (если нужен уровень TRACE).
# Асинхронность
# Для asyncio-приложений можно сделать асинхронные версии методов (через loop.run_in_executor).
# Метрики
# Рекомендую отслеживать: commands_processed, conflicts_detected, sync_duration.
# Тесты
# Unit-тесты на все методы: правильность формата, включение стектрейса, отсутствие дублирования handlers.
# Производительность
# При высоком трафике логирования — использовать QueueHandler и отдельный writer-thread.
# Безопасность
# Контекст может содержать PII; продумать фильтрацию/маскирование перед выводом.

