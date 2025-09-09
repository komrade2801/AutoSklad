from typing import Optional
from sqlalchemy.orm import Session

from DB.BaseCRUD import CoreEngine
from DB.Models.OperationsConsumptionHasDevice import OperationsConsumptionHasDevice


class EngineOperationsConsumptionHasDevice(CoreEngine):
    """
    Репозиторий для сущности OperationsConsumptionHasDevice.
    Предоставляет CRUD-операции и методы работы с привязкой
    операций потребления к устройствам на основе CoreEngine.
    """

    def __init__(self, session: Session = None):
        """
        Инициализация репозитория.

        :param session: Сессия SQLAlchemy; если None, CoreEngine сам получит её.
        """
        super().__init__(session=session, model=OperationsConsumptionHasDevice)

    def add_link(self, operations_consumption_id: int, device_id: int) -> bool:
        """
        Создаёт связь OperationsConsumption ↔ Device.

        Если такая связь уже есть — возвращает True.

        :param operations_consumption_id: ID операции потребления.
        :param device_id: ID устройства.
        :return: True при успешном создании или существовании.
        """
        # Проверяем наличие через CoreEngine.filter_by
        existing = self.filter_by(
            operations_consumption_id=operations_consumption_id,
            device_id=device_id
        )
        if existing:  # возвращает список, непустой — связь есть
            return True

        try:
            # Используем CoreEngine.add, который сам создаёт экземпляр и коммитит
            # add принимает id=… и остальные поля, поэтому:
            return self.add(
                operations_consumption_id=operations_consumption_id,
                device_id=device_id
            )
        except RuntimeError as e:
            # Игнорируем уникальный конфликт
            if "UNIQUE constraint failed" in str(e):
                return True
            raise

    def get_link(
            self, operations_consumption_id: int, device_id: int
    ) -> Optional[OperationsConsumptionHasDevice]:
        """
        Возвращает связь OperationsConsumption ↔ Device или None.

        Использует только методы CoreEngine (filter_by), без прямого доступа к session.

        :param operations_consumption_id: ID операции потребления.
        :param device_id: ID устройства.
        :return: Экземпляр OperationsConsumptionHasDevice или None.
        """
        results = self.filter_by(
            operations_consumption_id=operations_consumption_id,
            device_id=device_id
        )
        return results[0] if results else None

    def get_all_links(self) -> list[OperationsConsumptionHasDevice]:
        """
        Возвращает все записи привязок.

        :return: Список OperationsConsumptionHasDevice.
        """
        return self.all()

    def delete_link(
            self, operations_consumption_id: int, device_id: int
    ) -> bool:
        """
        Удаляет все связи OperationsConsumption ↔ Device по заданным ключам.

        Использует только методы CoreEngine: filter_by для поиска и transaction для удаления.

        :param operations_consumption_id: ID операции потребления.
        :param device_id: ID устройства.
        :return: True, если удалена хотя бы одна запись.
        """
        # Находим все подходящие сущности через CoreEngine.filter_by
        instances = self.filter_by(
            operations_consumption_id=operations_consumption_id,
            device_id=device_id
        )
        if not instances:
            return False

        # Удаляем каждую в рамках транзакции CoreEngine.transaction
        try:
            with self.transaction() as db:
                for inst in instances:
                    db.delete(inst)
            # Очищаем кеш CoreEngine после успешного удаления
            self._cache.clear()
            return True
        except RuntimeError:
            # В случае ошибки транзакции можно логировать или пробросить дальше
            raise
