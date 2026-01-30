from typing import Dict, List, Any, Protocol, Optional, TypedDict, Union
from .MappingConfigurator import MappingConfigurator
from .DiagnosticLogger import DiagnosticLogger


class DataConflictStrategy(Protocol):
    """
    Интерфейс стратегии разрешения конфликтов данных.
    """
    def resolve(self, local: Dict[str, Any], remote: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        ...


class LWWStrategy:
    """Last-Write-Wins: выбирает удалённые данные."""
    def resolve(self, local: Dict[str, Any], remote: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        return remote


class MergeFieldsStrategy:
    """Сливает поля, предпочитая значения remote при пересечении."""
    def resolve(self, local: Dict[str, Any], remote: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        merged = local.copy()
        merged.update(remote)
        return merged


class VectorClockStrategy:
    """
    Заглушка для стратегии VectorClock.
    Можно расширить отдельным классом с анализом векторов времени.
    """
    def resolve(self, local: Dict[str, Any], remote: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        # TODO: реализовать алгоритм VectorClock
        return remote


class ServerCommand(TypedDict):
    """
    Внутреннее представление команды синхронизации.
    """
    table: str
    data: Dict[str, Any]


class ConflictManager:
    """
    Управляет обнаружением и разрешением конфликтов при синхронизации данных и схем.

    Место в архитектуре:
        • Вызывается из SyncProcessor при обработке входящих команд (push).
        • Сначала проверяет и разрешает структурные конфликты, затем — конфликт полей данных.
        • Использует MappingConfigurator для ручного решения схемных разногласий.
        • Поддерживает внедрение пользовательских стратегий через registry.

    Зависимости:
        :param mapping_config: MappingConfigurator — для ручного разрешения схемных конфликтов.
        :param logger: DiagnosticLogger — для логирования этапов обнаружения и разрешения.
    """

    def __init__(
        self,
        mapping_config: MappingConfigurator,
        logger: Optional[DiagnosticLogger] = None
    ) -> None:
        self.mapping_config = mapping_config
        self.logger = logger
        # Реестр стратегий для данных
        self._data_strategies: Dict[str, DataConflictStrategy] = {
            "LWW": LWWStrategy(),
            "MergeFields": MergeFieldsStrategy(),
            "VectorClock": VectorClockStrategy()
        }

    def register_data_strategy(self, name: str, strategy: DataConflictStrategy) -> None:
        """
        Регистрирует новую стратегию разрешения конфликтов данных.

        :param name: Идентификатор стратегии.
        :param strategy: Объект, реализующий интерфейс DataConflictStrategy.
        """
        self._data_strategies[name] = strategy
        if self.logger:
            self.logger.log_info(f"Registered data conflict strategy: {name}")

    def detect_structure_conflict(
        self,
        client_fields: List[str],
        server_fields: List[str]
    ) -> List[str]:
        """
        Находит поля, присутствующие у клиента или сервера, но отсутствующие у другой стороны.

        :return: Список конфликтующих имён полей.
        """
        missing_on_server = [f for f in client_fields if f not in server_fields]
        missing_on_client = [f for f in server_fields if f not in client_fields]
        conflicts = missing_on_server + missing_on_client
        if self.logger and conflicts:
            self.logger.log_debug(f"Structure conflicts detected: {conflicts}")
        return conflicts

    def apply_structure_strategy(
        self,
        table: str,
        conflicts: List[str],
        strategy: str = "manual",
        **kwargs
    ) -> Dict[str, str]:
        """
        Разрешает конфликт схемы, возвращая маппинг remote_field → local_field.

        :param table: Название таблицы.
        :param conflicts: Список полей в конфликте.
        :param strategy:
            - "manual": MappingConfigurator.on_conflict(...)
            - "drop": отбрасывает все конфликтующие поля
            - "default": оставляет только общие поля (из common_fields в kwargs)
        :return: Словарь соответствий.
        :raises RuntimeError: если для manual не передан configurator.
        """
        if strategy == "drop":
            return {}

        if strategy == "default":
            common = kwargs.get("common_fields", [])
            mapping = {f: f for f in conflicts if f in common}
            if self.logger:
                self.logger.log_debug(f"Default structure mapping: {mapping}")
            return mapping

        if strategy == "manual":
            configurator: MappingConfigurator = kwargs.get("configurator") or self.mapping_config
            mapping = configurator.on_conflict(src_table=table, dst_table=conflicts, ambiguous_fields=None)
            if self.logger:
                self.logger.log_info(f"Manual structure mapping for {table}: {mapping}")
            return mapping

        raise ValueError(f"Unknown structure strategy: {strategy}")

    def detect_data_conflict(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any]
    ) -> bool:
        """
        Сравнивает словари по ключам и значениям.

        :return: True, если данные отличаются.
        """
        conflict = local_data != remote_data
        if self.logger and conflict:
            self.logger.log_debug(f"Data conflict: local={local_data}, remote={remote_data}")
        return conflict

    def apply_data_strategy(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any],
        strategy: str = "LWW",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Разрешает конфликт значений через выбранную стратегию.

        Для LWW: нормализация id/index, при конфликте status_id приоритет у локальных
        данных (чтобы не затирать выдачу/в процессе данными сервера). Исключение: при
        remote_status_stype in (mass_load_init, mass_load_ready, mass_drop_init, mass_drop_ready)
        входящие данные принимаются.
        
        КРИТИЧЕСКОЕ ПРАВИЛО для Cell: локальные активные операции (load_ready, mass_load_ready)
        защищены от затирания, НО массовые операции с сервера имеют приоритет.

        :param strategy: Ключ стратегии из зарегистрированных.
        :return: Объединённый или выбранный результат.
        :raises KeyError: если стратегия не найдена.
        """
        if strategy in ("last_write_wins", "LWW"):
            remote_norm = dict(remote_data)
            if "index" in remote_norm and "id" not in remote_norm:
                remote_norm["id"] = remote_norm.pop("index")
            remote_status_stype = kwargs.get("remote_status_stype")
            table = kwargs.get("table")
            
            # === КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Для Cell добавляем защиту локальных активных операций ===
            if table == "Cell":
                local_status_id = local_data.get("status_id")
                remote_status_id = remote_norm.get("status_id")
                local_status_stype = kwargs.get("local_status_stype")
                
                # 1. Массовые операции с сервера имеют приоритет (даже над активными операциями)
                if remote_status_stype in ("mass_load_init", "mass_load_ready", 
                                            "mass_drop_init", "mass_drop_ready"):
                    merged = dict(local_data)
                    merged.update(remote_norm)
                    if self.logger:
                        self.logger.log_info(
                            "LWW: accepting remote (mass operation)",
                            {
                                "remote_status_stype": remote_status_stype,
                                "local_status_id": local_status_id,
                                "remote_status_id": remote_status_id
                            },
                        )
                    return merged
                
                # 2. Защита локальных активных операций (load_ready, mass_load_ready)
                # Проверяем по stype, если доступен, иначе по status_id (3 или 7)
                if local_status_id:
                    is_active_operation = False
                    if local_status_stype:
                        # Проверяем по stype (надежнее)
                        is_active_operation = local_status_stype in ("load_ready", "mass_load_ready")
                    elif local_status_id in (3, 7):
                        # Fallback: проверяем по status_id (3 = mass_load_ready, 7 = load_ready)
                        is_active_operation = True
                    
                    if is_active_operation:
                        # Исключение: массовые операции с сервера уже обработаны выше
                        # Здесь защищаем от других операций
                        if self.logger:
                            self.logger.log_info(
                                "LWW: keeping local data (active operation)",
                                {
                                    "local_status_stype": local_status_stype or f"status_id={local_status_id}",
                                    "local_status_id": local_status_id,
                                    "remote_status_id": remote_status_id,
                                    "remote_status_stype": remote_status_stype
                                },
                            )
                        return local_data
                
                # 3. Для Cell в остальных случаях — стандартная логика по status_id
                if local_status_id and remote_status_id:
                    if local_status_id != remote_status_id:
                        if self.logger:
                            self.logger.log_info(
                                "LWW: keeping local data (status_id differs)",
                                {
                                    "local_status_id": local_status_id, 
                                    "remote_status_id": remote_status_id
                                },
                            )
                        return local_data
            
            # === СТАНДАРТНАЯ ЛОГИКА для остальных таблиц ===
            # Массовая загрузка: при remote_stype mass_load_init/mass_load_ready принимаем входящие
            if remote_status_stype in ("mass_load_init", "mass_load_ready"):
                merged = dict(local_data)
                merged.update(remote_norm)
                if self.logger:
                    self.logger.log_info(
                        "LWW: accepting remote (mass_load)",
                        {"remote_status_stype": remote_status_stype},
                    )
                return merged
            # Массовая выгрузка: при remote_stype mass_drop_init/mass_drop_ready принимаем входящие,
            # иначе ячейки не переходят в «Объявлена массовая выгрузка» и write_db_drop_tool_groups не находит их
            if remote_status_stype in ("mass_drop_init", "mass_drop_ready"):
                merged = dict(local_data)
                merged.update(remote_norm)
                if self.logger:
                    self.logger.log_info(
                        "LWW: accepting remote (mass_drop)",
                        {"remote_status_stype": remote_status_stype},
                    )
                return merged
            if "status_id" in local_data and "status_id" in remote_norm:
                if local_data["status_id"] != remote_norm["status_id"]:
                    # Если это НЕ таблица Cell, мы позволяем серверу обновлять статус (например, Load закрывается)
                    # Если таблица Cell, то логика выше уже обработала это (возвратом local_data или merged)
                    # Но если Cell попала сюда (например, remote не mass_load и local не active),
                    # то мы должны решить: защищать ли локальный статус 1 (свободно) от удаленного 7 (занято)?
                    # Выше мы уже защитили active (7/3).
                    # Если здесь local=1, remote=7 -> Differs -> Keep Local. (Защищает от "замерзания" в занятом состоянии)
                    
                    if table == "Cell":
                        if self.logger:
                            self.logger.log_info(
                                "LWW: keeping local data (status_id differs for Cell)",
                                {
                                    "local_status_id": local_data["status_id"], 
                                    "remote_status_id": remote_norm["status_id"]
                                },
                            )
                        return local_data
                    
                    # Для остальных таблиц (Load, History и т.д.) мы разрешаем обновление статуса от сервера (LWW)
                    # Чтобы сервер мог закрывать операции.
                    pass

            merged = dict(local_data)
            merged.update(remote_norm)
            if self.logger:
                self.logger.log_info(f"Applied data strategy 'LWW' (merged) result keys: {list(merged.keys())}")
            return merged

        strat = self._data_strategies.get(strategy)
        if not strat:
            raise KeyError(f"Data strategy '{strategy}' is not registered")
        result = strat.resolve(local_data, remote_data, **kwargs)
        if self.logger:
            self.logger.log_info(f"Applied data strategy '{strategy}' result: {result}")
        return result

    def resolve(
        self,
        existing: Dict[str, Any],
        incoming: ServerCommand,
        schema_fields: Dict[str, List[str]],
        data_strategy: str = "LWW",
        structure_strategy: str = "manual"
    ) -> Dict[str, Any]:
        """
        Единый метод обнаружения и разрешения конфликтов для одной команды.

        1. detect_structure_conflict → apply_structure_strategy
        2. map fields via MappingConfigurator
        3. detect_data_conflict → apply_data_strategy

        :param existing: Существующая запись из БД.
        :param incoming: Оригинальный incoming command с полями.
        :param schema_fields: {'client': [...], 'server': [...]}.
        :return: Готовый к применению словарь полей.
        """
        # 1. Структурные
        conf = self.detect_structure_conflict(schema_fields['client'], schema_fields['server'])
        if conf:
            mapping = self.apply_structure_strategy(
                incoming['table'], conf,
                strategy=structure_strategy,
                common_fields=list(set(schema_fields['client']) & set(schema_fields['server']))
            )
        else:
            mapping = {f: f for f in schema_fields['client']}

        # 2. Map incoming data
        mapped: Dict[str, Any] = {
            mapping.get(k, k): v
            for k, v in incoming['data'].items()
            if mapping.get(k, k) in existing or k in mapping
        }

        # 3. Данные
        if self.detect_data_conflict(existing, mapped):
            return self.apply_data_strategy(existing, mapped, strategy=data_strategy, timestamp=incoming.get('last_modified'))
        return mapped


# Список изменений:
# Внедрение паттерна Strategy
# – Отдельные классы LWWStrategy, MergeFieldsStrategy, VectorClockStrategy реализуют интерфейс DataConflictStrategy.
# – Метод register_data_strategy позволяет динамически добавлять новые алгоритмы.
#
# Protocol для стратегии
# – Используется typing.Protocol для описания контракта стратегий.
#
# Единый метод resolve
# – Объединяет логику обнаружения и разрешения конфликтов структуры и данных в одном месте.
#
# TypedDict ServerCommand
# – Строгая типизация входящей команды.
#
# Logging через DiagnosticLogger
# – Информация об этапах: обнаружение, маппинг, применение стратегии.
#
# Гибкая конфигурация
# – Параметры data_strategy и structure_strategy задаются при вызове.
#
# Докстринги
# – Описывают архитектуру, зависимости, протокол вызовов и примеры страт.
#
# Дополнительная информация и рекомендации:
# MappingConfigurator
# – Метод on_conflict должен принимать (table: str, conflicts: List[str]) и возвращать Dict[remote_field, local_field].
#
# Метрики
# – Счётчики конфликтов: по таблицам, по стратегиям.
#
# Unit-тесты
# – Проверить все ветки apply_structure_strategy и apply_data_strategy.
#
# Расширение
# – Подключение внешних реализаций стратегий через entry_points.
#
# Производительность
# – Для больших объектов данных можно рассмотреть diff‐алгоритмы или инкрементальное применение.
#
# Документация
# – Рекомендую добавить sequence-diagram в документацию проекта (PlantUML).
#
# Валидация
# – Подумать о валидации входящих полей через Pydantic-модели перед разрешением.