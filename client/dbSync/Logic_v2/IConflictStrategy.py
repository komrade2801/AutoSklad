from abc import ABC, abstractmethod
from typing import Any, Dict, Protocol, runtime_checkable


class IConflictStrategy(Protocol):
    """
    Интерфейс стратегии разрешения конфликтов данных в процессе синхронизации.

    Место в архитектуре:
        • Определяет контракт для алгоритма объединения двух версий записи (локальной и удалённой).
        • Используется внутри ConflictManager для выбора конкретной стратегии.
        • Интегрируется через ConflicManager.get_strategy и применяется SyncProcessor.

    Зависимости:
        Не зависит от внешних сервисов, оперирует только двумя словарями данных.

    Основная ответственность:
        Принимать два набора полей и возвращать единый, готовый к сохранению.

    Протокол:
        strategy.resolve(local: dict, remote: dict) -> dict
    """

    @abstractmethod
    def resolve(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Объединяет или выбирает поля из local_data и remote_data.

        :param local_data: Текущие данные записи из локальной БД.
        :param remote_data: Входящие данные из команды синхронизации.
        :return: Итоговый словарь полей для сохранения.
        """
        ...


class LWWStrategy:
    """
    Last-Write-Wins:
    Стратегия, которая при конфликте отдаёт приоритет удалённым данным.

    Использование:
        • Подходит для сценариев, где удалённая сторона считается авторитетной.
    """

    def resolve(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Возвращает remote поверх local
        return {**local_data, **remote_data}


class MergeFieldsStrategy:
    """
    MergeFields:
    Стратегия по-полям объединения:
    • Сохраняет все локальные поля,
    • Перезаписывает их удалёнными, если присутствуют,
    • Не удаляет отсутствующие в incoming.
    """

    def resolve(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        merged = local_data.copy()
        merged.update(remote_data)
        return merged


class VectorClockStrategy:
    """
    VectorClock:
    Стратегия на основе векторов времени:
    • Ожидает, что значение каждого поля представлено как {"value":..., "ts":...}.
    • Для каждого поля выбирает более "свежую" версию по ts.
    • Если структура не соответствует, fallback на remote.
    """

    def resolve(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        keys = set(local_data) | set(remote_data)
        for key in keys:
            l = local_data.get(key)
            r = remote_data.get(key)
            if isinstance(l, dict) and isinstance(r, dict) and 'ts' in l and 'ts' in r:
                # Сравнение ISO-ts
                if l['ts'] >= r['ts']:
                    result[key] = l
                else:
                    result[key] = r
            else:
                # По умолчанию — удалённая, если не None
                result[key] = r if r is not None else l
        return result

# ----------------------------------------------------------------------------
# Внедрение в ConflictManager:
#
# class ConflictManager:
#     def __init__(self, config_crud: SyncConfigCRUD):
#         self.strategies: Dict[str, IConflictStrategy] = {
#             'LWW': LWWStrategy(),
#             'MERGE': MergeFieldsStrategy(),
#             'VECTOR': VectorClockStrategy(),
#         }
#
#     def get_strategy(self, table_name: str) -> IConflictStrategy:
#         name = self.config_crud.get_strategy(table_name) or 'LWW'
#         return self.strategies.get(name.upper(), self.strategies['LWW'])
#
#     def apply_data_strategy(self, local, remote, table_name):
#         strat = self.get_strategy(table_name)
#         return strat.resolve(local, remote)
#
# SyncProcessor._process_single:
#     existing = ...
#     incoming = data_mapper.map_incoming(...)
#     if conflict_manager.detect_data_conflict(existing, incoming):
#         resolved = conflict_manager.apply_data_strategy(existing, incoming, table_name)
#     else:
#         resolved = incoming
#     crud.update(resolved)
#
# Таким образом, IConflictStrategy полностью покрывает все функции по объединению версий данных.
# ----------------------------------------------------------------------------
# Список изменений
# Интерфейс Protocol
# – IConflictStrategy переопределён как typing.Protocol с абстрактным методом resolve, а не ABC, для гибкости DI.
#
# Полные докстринги
# – Описывают место в архитектуре, ответственность и протокол вызовов.
#
# Единообразные сигнатуры
# – Все реализации принимают local_data: Dict[str, Any], remote_data: Dict[str, Any], возвращают Dict[str, Any].
#
# VectorClockStrategy
# – Улучшена проверка наличия ts и сравнение строк ISO, fallback на удалённую сторону.
#
# Интеграция
# – Пример кода для ConflictManager.get_strategy и apply_data_strategy.
#
#  Дополнительная информация и рекомендации
# Регистрация стратегий
# – Можно вынести регистрацию в ConflictManager.register_strategy(name, strategy) для расширяемости.
#
# Конфигурация
# – SyncConfigCRUD или SyncSettings должен хранить маппинг таблица→стратегия.
#
# Метрики
# – Счётчики conflict_detected, strategy_applied_{name} для мониторинга.
#
# Тесты
# – Unit-тесты для каждой стратегии с разнообразными сценариями данных (включая некорректные форматы).
#
# Улучшения
# – Добавить стратегию ThreeWayMerge: три версии (local, base, remote).
# – В VectorClockStrategy поддержать сравнение не только строк, но и числовых векторов.
#
# Производительность
# – Для больших объектов использовать lazy-просчёт полей (генераторы).