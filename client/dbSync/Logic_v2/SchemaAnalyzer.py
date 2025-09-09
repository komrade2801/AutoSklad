from typing import Any, Dict, Callable, Optional, List
from .DiagnosticLogger import DiagnosticLogger
from typing import Dict, Any, Tuple, Optional, Set, List

field = {
    ("Tools",      "inventory_number"): "barcode",
    ("ToolTypes",  "groups_id"):       "groups_id",
    # … любые другие «особые» кейсы …
}

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
    # Dict: Optional[Dict[Tuple[str, str], str]]
    def __init__(
            self,
            comparator: Optional[
                Callable[
                    [Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]],
                    Dict[str, Dict[str, str]]
                ]
            ] = None,
            logger: Optional[DiagnosticLogger] = None
    ) -> None:
        self._comparator = comparator or self._default_comparator #_universal_comparator
        self.logger = logger

    def generate_mapping(
            self,
            src_schema: Dict[str, Dict[str, Any]],
            dst_schema: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, str]]:
        """
        Строит карту соответствий полей между двумя схемами.

        :param src_schema: Структура источника вида {table: {field: type, ...}, ...}
        :param dst_schema: Структура приёмника того же формата.
        :return: dict, где ключ — имя таблицы, значение — словарь src_field -> dst_field.
        :raises ValueError: если структуры некорректны.
        """
        if not isinstance(src_schema, dict) or not isinstance(dst_schema, dict):
            raise ValueError("Schemas must be dicts of table->fields mappings")
        mapping = self._comparator(src_schema, dst_schema, field)
        if self.logger:
            self.logger.log_info(
                "Generated initial schema mapping",
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
            dst: Dict[str, Dict[str, Any]],
            field_aliases: Optional[Dict[Tuple[str, str], str]] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        Базовый алгоритм: для каждой таблицы делаем 1:1 по совпадающим именам полей.

        :param src: Исходная схема.
        :param dst: Целевая схема.
        :return: Черновая карта соответствий.
        """
        result: Dict[str, Dict[str, str]] = {}
        for table, src_fields in src.items():
            dst_fields = dst.get(table, {})
            field_map: Dict[str, str] = {}
            for field in src_fields:
                if field in dst_fields:
                    field_map[field] = field
                else:
                    # можно вставить fuzzy matching здесь
                    pass
            if field_map:
                result[table] = field_map
        return result

    def _universal_comparator(
            self,
            src_schema: Dict[str, Dict[str, Any]],
            dst_schema: Dict[str, Dict[str, Any]],
            field_aliases: Optional[Dict[Tuple[str, str], str]] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        «Универсальный» компаратор, который:
          1. Пытается найти прямую таблицу src → таблицу dst (по совпадению имени).
          2. Если прямого совпадения нет, пробует склеить две (или более) таблицы src в одну таблицу dst,
             ориентируясь на поля вида <X>_id (FK → родительская таблица).
          3. Поддерживает «псевдонимы» полей (field_aliases), например, inventory_number → barcode.

        :param src_schema:    Словарь {имя_таблицы: {имя_поля: тип, …}, …} для «серверной» схемы.
        :param dst_schema:    Словарь {имя_таблицы: {имя_поля: тип, …}, …} для «устройственной» схемы.
        :param field_aliases: Опциональный словарь { (src_table, src_field) → dst_field },
                              чтобы явно задать соответствия (например, ("Tools","inventory_number"):"barcode").
        :return:              Словарь вида { dst_table: { src_field → dst_field, … }, … }.
        """

        field_aliases = field_aliases or {}

        # Сначала соберём список «родительских» отношений в src_schema по простому правилу <имя>_id:
        #   – Если в src_schema[A] есть колонка “tool_type_id”, то предполагаем, что есть таблица “ToolTypes” (или “toolType”).
        #   – Для универсальности мы будем искать ВСЕ таблицы B, у которых имя B.lower() == “tooltype”.
        #
        # В итоге relations будет списком кортежей (child_table, parent_table, fk_field).
        relations: List[Tuple[str, str, str]] = []
        for child_table, fields in src_schema.items():
            for col in fields.keys():
                if col.endswith("_id"):
                    # потенциальная таблица-родитель (берём «корень» имени перед "_id")
                    parent_candidate = col[:-3]  # например, "tool_type"
                    # Попробуем найти в src_schema таблицу, чьё имя case-insensitive совпадает с parent_candidate
                    for parent_table in src_schema:
                        if parent_table.lower() == parent_candidate.lower() or \
                                parent_table.lower() == (parent_candidate + "s").lower() or \
                                (parent_table + "s").lower() == parent_candidate.lower():
                            relations.append((child_table, parent_table, col))
        # relations теперь может содержать, например, [("Tools", "ToolTypes", "tool_type_id"), …]

        result: Dict[str, Dict[str, str]] = {}

        # Вспомогательная функция: пытается составить маппинг между полями из src_fields и dst_fields,
        # учитывая alias (из field_aliases) и точные совпадения:
        def map_fields_simple(
                src_table: str,
                src_fields: Set[str],
                dst_fields: Set[str]
        ) -> Dict[str, str]:
            mapping: Dict[str, str] = {}

            # 1) Сначала пробегаем все alias'ы, относящиеся к этой src_table:
            for (t, f_src), f_dst in field_aliases.items():
                if t == src_table and f_src in src_fields and f_dst in dst_fields:
                    mapping[f_src] = f_dst

            # 2) Затем делаем все точные совпадения по имени поля:
            for f in src_fields:
                if f in dst_fields:
                    mapping[f] = f  # src_field → dst_field с таким же именем

            return mapping

        # Основная логика: для каждой dst_table пробуем найти, как её «собрать» из src_schema
        for dst_table, dst_cols_dict in dst_schema.items():
            dst_fields: Set[str] = set(dst_cols_dict.keys())

            # 1) Если есть src_table с точно таким же именем (без учёта регистра) — пытаемся сделать простой 1:1 маппинг:
            matched_directly: Optional[str] = None
            for src_table in src_schema:
                if src_table.lower() == dst_table.lower():
                    matched_directly = src_table
                    break

            if matched_directly:
                src_fields = set(src_schema[matched_directly].keys())
                field_map = map_fields_simple(matched_directly, src_fields, dst_fields)
                if field_map:
                    result[dst_table] = field_map
                    continue
                # Если даже при совпадении имён не нашлось ни одного поля → пробуем идти дальше.

            # 2) Если прямого совпадения не было (или поля не совпали), пробуем «склеить» одну или несколько таблиц из src:
            #    Ищем комбинацию из двух таблиц (child + parent), которые связаны через FK, и чей объединённый
            #    набор полей максимально «покрывает» dst_fields.

            best_combo: Optional[Dict[str, str]] = None
            best_cover: int = 0

            # Переберём все отношения child→parent, которые мы нашли
            for (child_table, parent_table, fk_field) in relations:
                # src_fields из child (без самого FK), плюс все src_fields из parent:
                child_fields = set(src_schema[child_table].keys()) - {fk_field}
                parent_fields = set(src_schema[parent_table].keys())

                # Попробуем объединить оба множества:
                combined_fields = child_fields.union(parent_fields)

                # Смэппим их на dst_fields через alias и точные совпадения:
                #  – для полей child_table берём map_fields_simple(child_table, child_fields, dst_fields)
                #  – для полей parent_table берём map_fields_simple(parent_table, parent_fields, dst_fields)
                map_child = map_fields_simple(child_table, child_fields, dst_fields)
                map_parent = map_fields_simple(parent_table, parent_fields, dst_fields)

                # Объединяем:
                merged_map = {**map_child, **map_parent}

                # Подсчитаем, сколько unique dst_fields мы «закрыли»:
                cover_count = len(set(merged_map.values()))

                # Если это покрытие лучше, чем текущее, запомним его:
                if cover_count > best_cover:
                    best_cover = cover_count
                    best_combo = {}
                    # заметим, что нам нужно знать, КАК именно сформировать dst_table из src:
                    #   – child_table.src_field → dst_field
                    #   – parent_table.src_field → dst_field
                    # Для ясности воспользуемся строковыми ключами "ChildTable.field"
                    for s_f, d_f in map_child.items():
                        best_combo[f"{child_table}.{s_f}"] = d_f
                    for s_f, d_f in map_parent.items():
                        best_combo[f"{parent_table}.{s_f}"] = d_f

            # Если удалось найти какую-то комбинацию, где хотя бы одно поле совпало, берём её:
            if best_combo and best_cover > 0:
                result[dst_table] = best_combo
                continue

            # 3) И наконец — случай, когда ни простое совпадение имён, ни пара «child→parent» не помогла.
            #    Тогда мы всё равно попытаемся делать маппинг field-by-field внутри ВСЕХ таблиц src,
            #    но будем считать, что dst_table соответствует сразу *всем* src-таблицам (что, может,
            #    избыточно, но универсально). Собираем «исходные» поля из всех src_table подряд…
            all_src_fields: Set[str] = set()
            for st, fld_dict in src_schema.items():
                all_src_fields |= set(fld_dict.keys())

            # Смэппим:
            fallback_map = map_fields_simple("<ALL_SRC>", all_src_fields, dst_fields)
            if fallback_map:
                result[dst_table] = fallback_map
            # Если и здесь ничего не нашлось, в result ничего не пишем (значит, dst_table без маппинга).

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
