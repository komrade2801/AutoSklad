import json
import os
import threading
import traceback
from datetime import datetime
from glob import glob
from typing import Any, Dict, Optional, List
import logging
from jsonschema import Draft7Validator, validate as js_validate, ValidationError, SchemaError
from .DiagnosticLogger import DiagnosticLogger
logger = logging.getLogger(__name__)


class JSONSchemaValidator:
    """
    Валидирует JSON-сообщения синхронизационного протокола по заранее определённым схемам.

    Схемы хранятся в директории Logic/schemas/, файл формата <schema_name>.json.
    При инициализации загружает все доступные схемы и компилирует валидаторы.

    Место в архитектуре:
      • Используется в TransportService для валидации payload перед отправкой и после приёма.
      • Отделяет проверку формата/контракта от бизнес-логики SyncProcessor.

    Зависимости:
      :param schema_dir: Путь к папке со схемами (по умолчанию рядом с файлом).
      :param logger:    (Optional) DiagnosticLogger для логирования ошибок валидации.

    Основные методы:
      - validate(payload: Any, schema_name: str) -> None
          Проверяет объект payload по указанной схеме.
          Бросает ValidationError или RuntimeError.

      - is_valid(payload: Any, schema_name: str) -> bool
          Возвращает True/False без исключений.

      - available_schemas() -> List[str]
          Возвращает список имён загруженных схем.

    Пример использования:
        validator = JSONSchemaValidator(logger=diag_logger)
        if not validator.is_valid(push_payload, 'push_commands'):
            diag_logger.log_error('Invalid push payload', {'stage':'send_push'})
            raise ValueError('Payload does not conform to schema')
        # или
        validator.validate(response_json, 'pull_response')
    """

    def __init__(
        self,
        schema_dir: Optional[str] = None,
        logger: Optional[DiagnosticLogger] = None
    ) -> None:
        self.logger = logger
        base_dir = schema_dir or os.path.join(os.path.dirname(__file__), 'schemas')
        self.schema_dir = base_dir
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._validators: Dict[str, Draft7Validator] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Загружает и компилирует все JSON-схемы из директории schema_dir."""
        pattern = os.path.join(self.schema_dir, '*.json')
        for path in glob(pattern):
            name = os.path.splitext(os.path.basename(path))[0]
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                # Проверяем валидность самой схемы
                Draft7Validator.check_schema(schema)
                self._schemas[name] = schema
                self._validators[name] = Draft7Validator(schema)
                if self.logger:
                    self.logger.log_debug(f"Loaded schema '{name}' from {path}")
                print(f'[ПОТОК][{threading.current_thread().name}][JSONSchemaValidator][_load_schemas][INFO] - Загружена схема: {name}. [{datetime.now()}]')
            except (json.JSONDecodeError, SchemaError, FileNotFoundError) as e:
                print(f'[ПОТОК][{threading.current_thread().name}][JSONSchemaValidator][_load_schemas][ERROR] - error: {e}, Не удалось загрузить схему {name} подробности: - {traceback.format_exc()}. [{datetime.now()}]')

                msg = f"Failed to load schema '{name}': {e}"
                if self.logger:
                    self.logger.log_error(msg, {'path': path})
                else:
                    raise RuntimeError(msg)

    def available_schemas(self) -> List[str]:
        """Возвращает список имён загруженных схем."""
        print(f'[ПОТОК][{threading.current_thread().name}][JSONSchemaValidator][available_schemas] - schemas: {list(self._schemas.keys())}. [{datetime.now()}]')
        return list(self._schemas.keys())

    def validate(self, payload: Any, schema_name: str) -> None:
        """
        Проверяет payload по схеме schema_name.

        :raises RuntimeError: если схема не найдена.
        :raises ValidationError: если payload не соответствует схеме.
        """
        print(f'[ПОТОК][{threading.current_thread().name}][JSONSchemaValidator][validate] - Проверяем payload по схеме schema_name: {schema_name}. [{datetime.now()}]')
        validator = self._validators.get(schema_name)
        if not validator:
            msg = f"Schema not found: '{schema_name}'"
            if self.logger:
                self.logger.log_error(msg, {'schema_name': schema_name})
            print(f'[ПОТОК][{threading.current_thread().name}][JSONSchemaValidator][validate][ERROR] - error: {msg}, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
            raise RuntimeError(msg)
        errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
        if errors:
            first = errors[0]
            msg = f"Validation failed for schema '{schema_name}': {first.message}"
            context = {
                'schema': schema_name,
                'error_path': list(first.path),
                'instance': first.instance
            }
            if self.logger:
                self.logger.log_error(msg, context)
            print(f'[ПОТОК][{threading.current_thread().name}][JSONSchemaValidator][validate][ERROR] - error: {msg}, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
            raise ValidationError(msg)

    def is_valid(self, payload: Any, schema_name: str) -> bool:
        """
        Быстрая проверка соответствия payload схеме.

        :return: True, если валидация успешна, иначе False.
        """
        try:
            self.validate(payload, schema_name)
            print(f'[ПОТОК][{threading.current_thread().name}][JSONSchemaValidator][is_valid][INFO] - Проверка соответствия payload. [{datetime.now()}]')
            return True
        except (ValidationError, RuntimeError) as e:
            print(f'[ПОТОК][{threading.current_thread().name}][JSONSchemaValidator][is_valid][ERROR][ValidationError, RuntimeError] - error: {e}, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
            return False


# Список изменений в обновлённой версии
# Динамическая загрузка всех схем
# – Используем glob для подгрузки всех *.json в schemas/.
# Отдельные Draft7Validator
# – Компиляция схем (Draft7Validator(schema)) один раз при старте.
# Методы is_valid и available_schemas
# – Быстрая проверка без исключений.
# – Получение списка доступных схем.
# Подробная диагностика ошибок
# – Сортировка ошибок, логирование первого с указанием пути и инстанса.
# – Использование DiagnosticLogger.
# Проверка на валидность самой схемы
# – Draft7Validator.check_schema(schema) при загрузке.
# Параметризация пути к схемам
# – schema_dir можно переопределить из конфигурации.
# Докстринги
# – Описывают архитектурное место, протокол вызовов и примеры.
# Прочая важная информация
# SchemaError
# – При некорректной схеме бросается SchemaError и логируется/прерывает старт, чтобы не работать с дефектными контрактами.
# Диагностика
# – log_debug при успешной загрузке схем.
# – log_error при любых проблемах.
# Performance
# – Схемы загружаются один раз, валидация идёт по предварительно скомпилированному валидатору.
# Предложения по улучшению
# Поддержка версий схем
# – Хранить схемы в поддиректориях v1/, v2/, выбирать по schema_name='v1/push_commands'.
# Кэширование ошибок
# – При частых невалидных payload, можно кэшировать последнее сообщение ошибки, чтобы не перегружать лог.
# Асинхронность
# – Для большого потока сообщений можно валидацию выносить в ThreadPoolExecutor.
# Расширение формата
# – Добавить поддержку draft-04/06 через опцию протокола.
# UI для схем
# – Генерировать документацию по схемам (Swagger/OpenAPI) автоматически.
# Unit-тесты
# – Тесты на загрузку всех схем, на валидацию корректных/некорректных JSON по каждой схеме.

