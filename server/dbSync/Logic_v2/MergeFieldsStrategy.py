from typing import Dict, Any #  , Protocol, runtime_checkable
from DiagnosticLogger import DiagnosticLogger
from IConflictStrategy import IConflictStrategy


class MergeFieldsStrategy(IConflictStrategy):
    """
    Стратегия разрешения конфликтов «Merge Fields»:

    При применении resolve(local_data, remote_data):
      • Формирует объединённый набор ключей из обеих версий.
      • Если поле присутствует только в одной версии — сохраняет его.
      • Если присутствует в обеих и значения совпадают — сохраняет.
      • Если значения различаются — отдаёт значение remote_data.

    Место в архитектуре:
      • Используется в ConflictManager как одна из стратегий (наряду с LWW, VectorClock).
      • SyncProcessor вызывает через ConflictManager.apply_data_strategy(), получает итоговую запись.

    Зависимости:
      :param logger: Optional[DiagnosticLogger] — для логирования этапа разрешения.

    Протокол вызовов:
      manager = ConflictManager(...)
      strat = manager.get_strategy(table_name)  # MergeFieldsStrategy()
      if manager.detect_data_conflict(local, incoming):
          merged = strat.resolve(local, incoming)
          # merged передаётся в CRUD
    """

    def __init__(self, logger: DiagnosticLogger = None) -> None:
        self.logger = logger

    def resolve(self, local_data: Dict[str, Any], remote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполняет merge-подход к объединению полей.

        :param local_data: Словарь текущих значений из локальной БД.
        :param remote_data: Словарь входящих данных из команды.
        :return: Новый словарь, объединяющий лучшие значения.
        """
        merged: Dict[str, Any] = {}
        for key in set(local_data) | set(remote_data):
            if key not in local_data:
                merged[key] = remote_data[key]
                if self.logger:
                    self.logger.log_debug(
                        "Field only in remote, taking remote", {"field": key, "value": remote_data[key]}
                    )
            elif key not in remote_data:
                merged[key] = local_data[key]
                if self.logger:
                    self.logger.log_debug(
                        "Field only in local, keeping local", {"field": key, "value": local_data[key]}
                    )
            elif local_data[key] == remote_data[key]:
                merged[key] = local_data[key]
                if self.logger:
                    self.logger.log_debug(
                        "Field equal in both, keeping value", {"field": key, "value": local_data[key]}
                    )
            else:
                merged[key] = remote_data[key]
                if self.logger:
                    self.logger.log_info(
                        "Conflict resolved by taking remote value", {"field": key, "local": local_data[key], "remote": remote_data[key]}
                    )
        return merged

# ----------------------------------------------------------------------------
# Изменения для полной поддержки:
# 1. Добавлен DiagnosticLogger для детального логирования по каждому полю.
# 2. Расширенный докстринг с описанием архитектуры, протокола вызовов и зависимостей.
# 3. Протокол Debug/Info для каждой ветки логики (only remote, only local, equal, conflict).
# 4. Типизация через typing.Dict и Any.
# 5. __init__ получает опциональный logger вместо жесткой зависимости.
#
# Прочая информация:
# - MergeFieldsStrategy сохраняет максимально полные данные, предпочтение удалённому на конфликтах.
# - Подходит, когда важно не терять данные, а конфликты локально разрешить в пользу remote.
# - Может быть расширена параметром fallback_strategy вместо жесткого remote.
#
# Рекомендации по улучшению:
# • Добавить параметр prefer_remote: bool, чтобы менять поведение при конфликте.
# • Поддержка nested-структур: рекурсивный merge.
# • Unit-тесты на сценарии: only-local, only-remote, equal, conflict.
# • Integration: использовать в ConflictManager.register_data_strategy('MergeFields', MergeFieldsStrategy()).
# ----------------------------------------------------------------------------
