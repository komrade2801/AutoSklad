import json
import os
from typing import Any, Dict, Callable, Optional  # , List
from .DiagnosticLogger import DiagnosticLogger


class SchemaAnalyzer:
    """
    Служба анализа и генерации карт соответствий между структурами баз данных источника и приёмника.

    Назначение:
        • При первом «handshake» или при изменении схемы определяет, как поля таблиц одного узла
          синхронизации соответствуют полям таблиц другого.
        • Генерирует «черновую» карту соответствий: по совпадающим именам и при необходимости
          вызывает расширенный алгоритм (fuzzy matching или пользовательский comparator).
        • Отвечает за детектирование изменений схем (по хешу или по содержанию) и инициирование
          перерасчёта mapping.

    Место в архитектуре:
        SyncProcessor.process_schema:
            1. Получает хеши client_schema и server_schema.
            2. Если хеш изменился или в кеше нет карты, вызывает generate_mapping().
            3. Сохраняет результат в SchemaCache.
        SyncProcessor._get_mapping:
            Лениво восстанавливает карту, если в кеше отсутствует.

    Зависимости:
        :param comparator: Optional[Callable[[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]], Dict[str, Dict[str, str]]]]
            Функция для пользовательского сравнения схем: принимает две структуры вида
            {table: {field: type}}, возвращает карту {table: {src_field: dst_field}}.
            По умолчанию используется `_default_comparator`.
        :param logger: Optional[DiagnosticLogger]
            Для логирования процесса генерации и ошибок.

    Основные методы:
        - generate_mapping(src_schema, dst_schema) -> Dict[str, Dict[str, str]]
            Возвращает карту соответствий всех таблиц и полей.
        - detect_changes(old_hash, new_hash) -> bool
            Сравнивает два хеша схем и возвращает True при различии.
        - _default_comparator(src, dst) -> Dict[str, Dict[str, str]]
            Простое 1:1 по совпадающим именам полей.

    Протокол вызовов (Sequence Diagram упрощённо):
        SyncProcessor -> SchemaAnalyzer: detect_changes(old_hash, new_hash)
        alt changed
            SyncProcessor -> SchemaAnalyzer: generate_mapping(src_schema, dst_schema)
            SchemaAnalyzer --> SyncProcessor: mapping
            SyncProcessor -> SchemaCache: set(client_hash, mapping)
        else unchanged
            SyncProcessor -> SchemaCache: get(client_hash)
        end
    """

    def __init__(
            self,
            comparator: Optional[
                Callable[
                    [Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]],
                    Dict[str, Dict[str, str]]
                ]
            ] = None,
            custom_fields_path: Optional[str] = None,
            logger: Optional[DiagnosticLogger] = None
    ) -> None:
        self._comparator = comparator or self._default_comparator
        self.logger = logger
        # путь по умолчанию внутри вашего проекта, если не передали явно
        if custom_fields_path is None:
            base = os.path.dirname(__file__)
            custom_fields_path = os.path.join(
                base, "cache", "fields", "sync_fields.json"
            )
        self._custom_fields_path = custom_fields_path
        self._custom: Dict[str, Dict[str, str]] = {}
        self._load_custom_fields()

    def _load_custom_fields(self) -> None:
        """Прочитать sync_fields.json один раз при инициализации."""
        try:
            with open(self._custom_fields_path, "r", encoding="utf-8") as f:
                self._custom = json.load(f)
            if self.logger:
                self.logger.log_info(
                    "Loaded custom sync_fields.json",
                    {"path": self._custom_fields_path, "tables": list(self._custom.keys())}
                )
        except FileNotFoundError:
            # если файла нет — просто пропускаем
            self._custom = {}
        except Exception as ex:
            # на всякий пожарный логируем ошибку
            if self.logger:
                self.logger.log_error("Failed to load custom fields", {
                    "path": self._custom_fields_path, "error": str(ex)
                })
            self._custom = {}

    def generate_mapping(
            self,
            src_schema: Dict[str, Dict[str, Any]],
            dst_schema: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, str]]:
        """
        Строит карту соответствий полей между двумя схемами,
        включая «особые» правила из sync_fields.json.
        """
        if not isinstance(src_schema, dict) or not isinstance(dst_schema, dict):
            raise ValueError("Schemas must be dicts of table->fields mappings")

        # 1) базовый маппинг по совпадающим именам
        mapping = self._comparator(src_schema, dst_schema)

        # 2) подмешиваем ваши «особые» таблицы/поля
        for table, fields_map in self._custom.items():
            # если таблица ещё не в маппинге — создаём пустой словарь
            mapping.setdefault(table, {})
            # затем обновляем (перезапишет любое standard-соответствие)
            mapping[table].update(fields_map)

        if self.logger:
            self.logger.log_info(
                "Generated schema mapping (with custom overrides)",
                {"tables": list(mapping.keys())}
            )
        return mapping

    def detect_changes(self, old_hash: str, new_hash: str) -> bool:
        """
        Определяет, изменилась ли схема.

        :param old_hash: Хеш предыдущей версии схемы.
        :param new_hash: Хеш текущей версии схемы.
        :return: True, если хеши отличаются.
        """
        changed = old_hash != new_hash
        if self.logger:
            self.logger.log_debug(
                "Schema change detected" if changed else "Schema unchanged",
                {"old_hash": old_hash, "new_hash": new_hash}
            )
        return changed

    def _default_comparator(
            self,
            src: Dict[str, Dict[str, Any]],
            dst: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, str]]:
        """
        Базовый алгоритм: 1:1 по совпадающим именам полей.
        """
        result: Dict[str, Dict[str, str]] = {}
        for table, src_fields in src.items():
            dst_fields = dst.get(table, {})
            field_map: Dict[str, str] = {}
            for field in src_fields:
                if field in dst_fields:
                    field_map[field] = field
            if field_map:
                result[table] = field_map
        return result

# Список изменений
# Расширенные докстринги
# – Описано место в архитектуре, протокол вызовов, зависимости и сценарии использования.
# Валидация входных данных
# – В generate_mapping проверяем, что схемы — словари корректного формата.
# Логирование
# – Через DiagnosticLogger в ключевых точках: генерация карты и детектирование изменений.
# Строгие сигнатуры
# – Явно описаны типы параметров и возвращаемого значения.
# Управляемые исключения
# – Бросаем ValueError при некорректных аргументах.
# Протокол Sequence Diagram
# – Включён блок «alt» для показательного порядка операций.
# Дополнительная информация и рекомендации
# Fuzzy Matching
# – Добавить алгоритмы Левенштейна или difflib.get_close_matches для автоматического сопоставления похожих полей.
# Кеширование
# – Интегрировать с SchemaCache, чтобы не пересчитывать mapping при каждом запросе.
# Версионирование
# – Поддержать разные версии схем (v1, v2) через параметризацию schema_name.
# Unit-тесты
# – Проверить все ветви: совпадающие поля, отсутствующие таблицы, пустые schemas.
# Performance
# – Для очень больших схем (100+ таблиц) распараллелить сравнительный проход по таблицам.
# Расширяемость
# – Позволить внешним модулям передавать comparator, возвращающий сложные маппинги (merge таблиц, разделение).
# Документация
# – Сгенерировать автоматическую документацию для всех public-методов в Swagger/OpenAPI.
