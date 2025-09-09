import json
import os
import threading
import traceback
from datetime import datetime
from typing import Dict, List, Callable, Optional, TypedDict, Any
import logging
from .DiagnosticLogger import DiagnosticLogger
logger = logging.getLogger(__name__)


class MappingConfig(TypedDict):
    """
    Тип хранимой конфигурации маппинга для одной таблицы.
    remote_field: local_field
    """


class MappingConfigurator:
    """
    Управляет соответствием полей между разноструктурными базами данных
    в процессе синхронизации.

    Место в архитектуре:
      • Используется в SyncProcessor при обнаружении структурных конфликтов.
      • Делегирует автоматическое или ручное разрешение через on_conflict.
      • Сохраняет постоянные маппинги в JSON-файл.

    Зависимости:
      :param mapping_source: путь к JSON-файлу с сохранёнными картами.
      :param manual_resolver: функция для ручного ввода соответствий
                              signature (table, fields)->Dict[str,str]
      :param logger: DiagnosticLogger для логирования действий.
    """

    def __init__(
        self,
        mapping_source: str = "mapping_config.json",
        manual_resolver: Optional[Callable[[str, List[str]], Dict[str, str]]] = None,
        logger: Optional[DiagnosticLogger] = None
    ) -> None:
        self.mapping_source = mapping_source
        self.logger = logger
        self.manual_resolver = manual_resolver
        self._lock = threading.Lock()
        self.mapping: Dict[str, MappingConfig] = self._load_mapping()

    def _load_mapping(self) -> Dict[str, MappingConfig]:
        """
        Загружает JSON-файл с картами соответствий.
        Если файл не существует или некорректен — возвращает пустую карту.
        """
        if not os.path.exists(self.mapping_source):
            return {}
        try:
            with open(self.mapping_source, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][_load_mapping] Загруженная конфигурация сопоставления. [{datetime.now()}]')
            return {k: v for k, v in data.items()}
        except Exception as e:
            print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][_load_mapping][ERROR] - error: {e} Не удалось загрузить сопоставление, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
            if self.logger:
                self.logger.log_error("Failed to load mapping", {"error": str(e)})
            return {}

    def _save_mapping(self) -> None:
        """
        Сохраняет текущее состояние self.mapping в JSON-файл.
        """
        try:
            with open(self.mapping_source, 'w', encoding='utf-8') as f:
                json.dump(self.mapping, f, indent=2, ensure_ascii=False)
            print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][_save_mapping] Сохраненная конфигурация сопоставления. [{datetime.now()}]')
        except Exception as e:
            print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][_load_mapping][ERROR] - error: {e} Не удалось загрузить сопоставление, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
            if self.logger:
                self.logger.log_error("Failed to save mapping", {"error": str(e)})

    def get_mapping_for_table(self, table: str) -> MappingConfig:
        """
        Возвращает карту соответствий для указанной таблицы.

        :param table: Имя таблицы.
        :return: Словарь remote_field->local_field.
        """
        return dict(self.mapping.get(table, {}))

    def list_tables(self) -> List[str]:
        """
        Список таблиц, для которых имеются сохранённые маппинги.
        """
        print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][list_tables] - tables: {list(self.mapping.keys())}. [{datetime.now()}]')
        return list(self.mapping.keys())

    def remove_mapping(self, table: str, remote_field: Optional[str] = None) -> None:
        """
        Удаляет маппинг:
          - Если remote_field=None — удаляет все маппинги для таблицы.
          - Иначе — удаляет только указанное поле.
        """
        print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][remove_mapping] - table: {table}, remote_field: {remote_field}. [{datetime.now()}]')
        with self._lock:
            if remote_field is None:
                self.mapping.pop(table, None)
                if self.logger:
                    self.logger.log_info("Removed all mappings for table", {"table": table})
            else:
                tbl = self.mapping.get(table)
                if tbl and remote_field in tbl:
                    tbl.pop(remote_field)
                    if self.logger:
                        self.logger.log_info("Removed mapping", {"table": table, "field": remote_field})
                        print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][remove_mapping] Удалена конфигурация сопоставления. [{datetime.now()}]')
            self._save_mapping()
        

    def export_mapping(self, dest_path: str) -> None:
        """
        Экспортирует всю текущую конфигурацию в указанный файл.
        """
        try:
            with open(dest_path, 'w', encoding='utf-8') as f:
                json.dump(self.mapping, f, indent=2, ensure_ascii=False)
            if self.logger:
                self.logger.log_info("Exported mapping config", {"dest": dest_path})
                print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][export_mapping] Экспортированная конфигурация сопоставления. [{datetime.now()}]')
        except Exception as e:
            print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][export_mapping][ERROR] - error: {e} Не удалось экспортировать сопоставление, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
            if self.logger:
                self.logger.log_error("Failed to export mapping", {"error": str(e)})

    def on_conflict(
        self,
        src_table: str,
        dst_table: str,
        ambiguous_fields: List[str]
    ) -> MappingConfig:
        """
        Вызывается при обнаружении конфликтных полей между структурами.

        1. Автоматически сопоставляет по имени (case-insensitive).
        2. Если manual_resolver задан — вызывает его для оставшихся.
        3. Сохраняет новые соответствия.

        :param src_table: Имя таблицы-источника.
        :param dst_table: Имя таблицы-приёмника.
        :param ambiguous_fields: Поля, требующие маппинга.
        :return: Новые пары remote_field->local_field.
        """
        new_map: MappingConfig = {}
        existing = self.get_mapping_for_table(src_table)

        if not ambiguous_fields:
            ambiguous_fields = []

        # 1. Автоматика по совпадению
        for field in ambiguous_fields:
            for local in existing.values():
                if local.lower() == field.lower():
                    new_map[field] = local
                    break

        # 2. Ручное разрешение
        remaining = [f for f in ambiguous_fields if f not in new_map]
        if remaining and self.manual_resolver:
            try:
                manual = self.manual_resolver(src_table, remaining)
                new_map.update(manual)
                print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][on_conflict] Ручное разрешение. [{datetime.now()}]')
            except Exception as e:
                print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][on_conflict][ERROR] - error: {e} Ошибка ручного распознавателя, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
                if self.logger:
                    self.logger.log_error("Manual resolver failed", {"error": str(e)})

        # 3. Сохранение
        if new_map:
            with self._lock:
                self.mapping.setdefault(src_table, {}).update(new_map)  # type: ignore
                self._save_mapping()
            if self.logger:
                self.logger.log_info("Resolved conflict mappings", {"table": src_table, "mappings": new_map})
            print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][on_conflict] Разрешенные сопоставления конфликтов. [{datetime.now()}]')

        return new_map

    def import_mapping(self, src_path: str) -> None:
        """
        Импортирует маппинги из внешнего JSON-файла,
        объединяя с текущими и сохраняя результат.
        """
        try:
            with open(src_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            with self._lock:
                for tbl, cfg in data.items():
                    self.mapping.setdefault(tbl, {}).update(cfg)
                self._save_mapping()
            if self.logger:
                self.logger.log_info("Imported mapping config", {"src": src_path})
            print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][import_mapping] Импортированная конфигурация сопоставления. [{datetime.now()}]')
        except Exception as e:
            print(f'[ПОТОК][{threading.current_thread().name}][MappingConfigurator][import_mapping][ERROR] - error: {e} Не удалось импортировать сопоставление, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
            if self.logger:
                self.logger.log_error("Failed to import mapping", {"error": str(e)})

# Список изменений:
# TypedDict MappingConfig
# — Чёткая структура remote_field → local_field.
# Потокобезопасность
# — Использован threading.Lock при модификациях self.mapping.
# DiagnosticLogger
# — Вместо logger. и неявных ошибок — централизованное логирование (log_info/log_error).
# manual_resolver
# — Внедрение callback-функции для ручного решения конфликтов, вместо ввода через input().
# Новые методы
# list_tables() — список всех таблиц с маппингом.
# remove_mapping() — удаление полного или частичного маппинга.
# export_mapping() и import_mapping() — для обмена конфигурациями.
# Улучшенный on_conflict
# — Шаги: автоматическая догадка → manual_resolver → сохранение и логирование.
# Докстринги
# — Полное описание архитектуры, зависимостей, примеры протоколов (внутри кода).
# Прочая важная информация:
# Ручное разрешение
# — manual_resolver(src_table, remaining_fields) → Dict[str,str] позволяет UI/CLI интеграции.
# Конфигурация
# — Путь к файлу mapping_source можно взять из централизованного конфига.
# Unit-тесты
# — Для всех новых методов (remove_mapping, export_mapping, import_mapping и on_conflict).
# Расширяемость
# — Можно добавить стратегии автосопоставления (например, Levenshtein), или ML-модель.
# Производительность
# — Для очень больших конфигураций использовать базу данных или кеши вместо JSON-файла.
# Миграции
# — При изменении формата маппинга поддерживать версионирование файла.
# Безопасность
# — Проверять, что manual_resolver не возвращает опасные значения (SQL-инъекции в именах полей).
