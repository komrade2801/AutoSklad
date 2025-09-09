import datetime
import logging
import threading
import traceback
from typing import Any, Dict, Callable, Optional, TypedDict, Union

from .DiagnosticLogger import DiagnosticLogger
logger = logging.getLogger(__name__)


class FieldMappings(TypedDict):
    """
    Словарь: remote_field -> local_field
    """
    # e.g.: "remoteName": "local_name"


class TypeMappings(TypedDict):
    """
    Словарь: local_field -> type_name
    type_name in {"datetime","int","float","bool"}
    """


class ConverterDict(TypedDict, total=False):
    """
    Словарь конвертеров для направления incoming/outgoing:
      "incoming": local_field->func
      "outgoing": local_field->func
    """
    incoming: Dict[str, Callable[[Any], Any]]
    outgoing: Dict[str, Callable[[Any], Any]]


class DataMapper:
    """
    Преобразует данные между JSON-контрактом клиента и локальной моделью БД.

    Место в архитектуре:
        • Используется в SyncProcessor перед CRUD-операциями (map_incoming).
        • Используется в SyncProcessor при сборке pull-ответа (map_outgoing).

    Зависимости:
        :param field_mappings: Dict[table, FieldMappings]
        :param type_mappings: Optional[Dict[table, TypeMappings]]
        :param converters: Optional[Dict[table, ConverterDict]]
        :param logger: Optional[DiagnosticLogger]

    Поток данных:
        incoming: JSON (remote_field keys) → local dict
        outgoing: local dict → JSON (remote_field keys)

    Протокол вызовов:
        SyncProcessor.process_push:
            local_data = mapper.map_incoming(table, remote)
            sync_manager.process_command(data=local_data)

        SyncProcessor.prepare_pull:
            raw = record_crud.fetch()
            remote = mapper.map_outgoing(table, raw)

    """

    def __init__(self,
                 field_mappings: Dict[str, Dict[str, str]],
                 type_mappings: Optional[Dict[str, Dict[str, Callable[[Any], Any]]]] = None,
                 custom_converters: Optional[Dict[str, Dict[str, Dict[str, Callable]]]] = None,
                 logger: Optional[DiagnosticLogger] = None,
                 converters: Optional[Dict[str, ConverterDict]] = None
                 ) -> None:
        """
        :param field_mappings: Словарь {table: {remoteField: local_field}}.
        :param type_mappings: Опциональный словарь {table: {local_field: type}} для приведения типов.
        :param custom_converters: Опциональный словарь конвертеров вида
               {table: {"incoming": {field: func}, "outgoing": {field: func}}}.
        """
        self.field_mappings = field_mappings or {}
        self.type_mappings = type_mappings or {}
        self.custom_converters = custom_converters or {}
        self.logger = logger
        self.converters = converters or {}

    def update_field_mappings(self, new_mappings: Dict[str, Dict[str, str]]) -> None:
        """
        Обновляет маппинг полей, на который опирается метод map_incoming/map_outgoing.
        """
        print(f'[ПОТОК][{threading.current_thread().name}][DataMapper] обновить сопоставления полей. Текущее время: {datetime.datetime.now()}')
        self.field_mappings = new_mappings or {}

    def map_incoming(self, table: str, record: Dict[str, Any], mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Преобразует JSON-запись (удаленный формат) в локальный формат.
        :param table: Название таблицы.
        :param record: Данные в JSON (ключи – remote поля).
        :param mapping: Дополнительный маппинг {remote_field: local_field}.
        :return: Словарь локальных полей.
        """
        result: Dict[str, Any] = {}
        if mapping:
            # Сначала применяем дополнительные соответствия
            record = {mapping.get(k, k): v for k, v in record.items()}
        base_map = self.field_mappings.get(table, {})
        converters = self.custom_converters.get(table, {}).get("incoming", {})
        type_map = self.type_mappings.get(table, {})
        print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_incoming] - table: {table}, record: {record}, base_map: {base_map}, converters: {converters}, type_map: {type_map}. Текущее время: {datetime.datetime.now()}')
        for remote_field, value in record.items():
            local_field = base_map.get(remote_field)
            if not local_field:
                continue
            if local_field in converters:
                try:
                    value = converters[local_field](value)
                except Exception as ex:
                    print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_incoming][ERROR] - error: {ex}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
                    continue
            elif local_field in type_map:
                try:
                    value = type_map[local_field](value)
                except Exception as ex:
                    print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_incoming][ERROR] - error: {ex}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
                    pass
            result[local_field] = value
        print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_incoming] - result: {result}. Текущее время: {datetime.datetime.now()}')
        return result

    def map_outgoing(self, table: str, record: Dict[str, Any], mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Преобразует локальную запись БД в формат JSON для клиента.
        :param table: Название таблицы.
        :param record: Локальные поля и их значения.
        :param mapping: Дополнительный маппинг {remote_field: local_field}.
        :return: Словарь готовый к сериализации (JSON-формат).
        """
        base_map = self.field_mappings.get(table, {})
        reverse_map = {local: remote for remote, local in base_map.items()}
        if mapping:
            inv = {local: remote for remote, local in mapping.items()}
            reverse_map.update(inv)
        converters = self.custom_converters.get(table, {}).get("outgoing", {})
        type_map = self.type_mappings.get(table, {})
        result: Dict[str, Any] = {}
        print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_outgoing] - table: {table}, record: {record}, base_map: {base_map}, converters: {converters}, type_map: {type_map}. Текущее время: {datetime.datetime.now()}')
        for local_field, value in record.items():
            remote_field = reverse_map.get(local_field)
            if not remote_field:
                continue
            if local_field in converters:
                try:
                    value = converters[local_field](value)
                except Exception as ex:
                    print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_outgoing][ERROR] - error: {ex}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
                    continue
            elif local_field in type_map:
                try:
                    value = type_map[local_field](value)
                except Exception as ex:
                    print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_outgoing][ERROR] - error: {ex}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
                    pass
            result[remote_field] = value
        print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_outgoing] - result: {result}. Текущее время: {datetime.datetime.now()}')
        return result

    def map_incoming_json_to_local(self, table: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует JSON-запись клиента в локальный формат.

        1. Находит локальное имя через field_mappings.
        2. Применяет custom converter (incoming) если задан.
        3. Иначе приводит тип по type_mappings.
        4. Логирует unmapped-поля как warning.

        :param table: Имя таблицы.
        :param record: Словарь remote_field->value.
        :return: Dict[local_field->typed_value].
        """
        mapping = self.field_mappings.get(table, {})
        type_map = self.type_mappings.get(table, {})
        conv = self.converters.get(table, {}).get('incoming', {})
        result: Dict[str, Any] = {}
        print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_incoming_json_to_local] - table: {table}, record: {record}, mapping: {mapping}, type_map: {type_map}, conv: {conv}. Текущее время: {datetime.datetime.now()}')
        for remote, value in record.items():
            local = mapping.get(remote)
            if not local:
                if self.logger:
                    self.logger.log_warning(f"Unmapped incoming field '{remote}' for table '{table}'")
                continue
            try:
                if local in conv:
                    result[local] = conv[local](value)
                elif local in type_map:
                    result[local] = self._to_local_type(value, type_map[local])
                else:
                    result[local] = value
            except Exception as e:
                print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_incoming_json_to_local][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
                if self.logger:
                    self.logger.log_error(f"Incoming converter error for '{local}': {e}")
                result[local] = value
        print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_incoming_json_to_local] - result: {result}. Текущее время: {datetime.datetime.now()}')
        return result

    def map_outgoing_local_to_json(self, table: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует локальную запись в JSON-формат для клиента.

        1. Строит обратное отображение local_field->remote_field.
        2. Применяет custom converter (outgoing) если задан.
        3. Иначе форматирует тип по type_mappings.
        4. Логирует unmapped-поля как warning.

        :param table: Имя таблицы.
        :param record: Dict[local_field->value].
        :return: Dict[remote_field->json_value].
        """
        rev = {v: k for k, v in self.field_mappings.get(table, {}).items()}
        type_map = self.type_mappings.get(table, {})
        conv = self.converters.get(table, {}).get('outgoing', {})
        result: Dict[str, Any] = {}
        print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_outgoing_local_to_json] - table: {table}, record: {record}, rev: {rev}, type_map: {type_map}, conv: {conv}. Текущее время: {datetime.datetime.now()}')
        for local, value in record.items():
            remote = rev.get(local)
            if not remote:
                if self.logger:
                    self.logger.log_warning(f"Unmapped outgoing field '{local}' for table '{table}'")
                continue
            try:
                if local in conv:
                    result[remote] = conv[local](value)
                elif local in type_map:
                    result[remote] = self._to_json_type(value, type_map[local])
                else:
                    result[remote] = value
            except Exception as e:
                print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_outgoing_local_to_json][ERROR] - error: {e}, Ошибка исходящего конвертера для {local}: подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
                if self.logger:
                    self.logger.log_error(f"Outgoing converter error for {local}: {e}")
                result[remote] = value
        print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_outgoing_local_to_json] - result: {result}. Текущее время: {datetime.datetime.now()}')
        return result

    def _to_local_type(self, value: Any, type_name: str) -> Any:
        """
        Приводит JSON-значение к Python-типу.
        Поддерживается datetime, int, float, bool.
        """
        try:
            print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_outgoing_local_to_json] - value: {value}, type_name: {type_name}. Текущее время: {datetime.datetime.now()}')
            if type_name == 'datetime':
                return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
            if type_name == 'int':
                return int(value)
            if type_name == 'float':
                return float(value)
            if type_name == 'bool':
                return bool(value)
        except Exception as e:
            print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_outgoing_local_to_json][ERROR] - error: {e}, Не удалось преобразовать тип для {value} в {type_name}: подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
            if self.logger:
                self.logger.log_error(f"Type conversion failed for '{value} to {type_name}: {e}")
        return value

    def _to_json_type(self, value: Any, type_name: str) -> Any:
        """
        Форматирует Python-тип в JSON-совместимый.
        """
        try:
            if type_name == 'datetime' and isinstance(value, datetime.datetime):
                print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_outgoing_local_to_json] - value: {value}, type_name: {type_name}. Текущее время: {datetime.datetime.now()}')
                return value.isoformat() + 'Z'
        except Exception as e:
            print(f'[ПОТОК][{threading.current_thread().name}][DataMapper][map_outgoing_local_to_json][ERROR] - error: {e}, Ошибка форматирования JSON для {value} подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
            if self.logger:
                self.logger.log_error(f"JSON formatting failed for '{value}': {e}")
        return value

#  Список изменений:
# TypedDict для конфигураций
# – FieldMappings, TypeMappings, ConverterDict описывают структуры field_mappings, type_mappings и converters.
#
# DiagnosticLogger
# – Опциональная зависимость logger вместо прямых logger. или logging.
#
# Упрощённые методы
# – map_incoming и map_outgoing читаются единообразно, с явным порядком: mapping → converter → типизация → fallback.
#
# Проверка unmapped-полей
# – Логируются как warning.
#
# Отдельные приватные методы для конверсий
# – _to_local_type и _to_json_type, с обработкой ошибок.
#
# Расширенный докстринг класса
# – Полное описание места в архитектуре, потока данных, протоколов вызовов.
#
#  Прочая важная информация:
# Не зависит напрямую от ORM: оперирует словарями, что упрощает тестирование и расширение.
#
# Поддержка custom converters: можно задавать функции на оба направления, без изменения ядра.
#
# Диагностика: логируется каждая ошибка конвертера, что ускоряет отладку маппингов.
#
#  Предложения по улучшению:
# Pydantic-модели
# – Использовать pydantic для валидации и авто-документирования маппингов.
#
# Асинхронность
# – Если нужна обработка больших объёмов, можно запускать map_incoming/map_outgoing в потоках.
#
# Метрики
# – Отслеживать количество unmapped-полей, время конверсий.
#
# Fallback-стратегии
# – Добавить строгую стратегию: выбрасывать исключение при unmapped, если в конфиге задан флаг strict.
#
# Тесты
# – Unit-тесты для всех веток (converter, type_mappings, unmapped) с фикстурами данных.
#
# Производительность
# – При больших записях использовать C-расширения или vectorized-преобразования (NumPy, pandas).
#
