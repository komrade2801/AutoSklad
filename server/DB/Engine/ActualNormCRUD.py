from datetime import datetime
from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.ActualNorm import ActualNorm

class EngineActualNorm(BaseCRUD):
    """
    Класс EngineActualNorm предоставляет интерфейс для работы с таблицей ActualNorm.
    Инкапсулирует CRUD-операции и обеспечивает удобные методы для управления квотами пользователей.
    """

    def __init__(self, session: Session=None):
        """
        Инициализация класса EngineActualNorm.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
        
        super().__init__(session=session, model=ActualNorm)

    def add_actual_norm(self, user_id: int, day: datetime) -> bool:
        """
        Добавляет новую квоту пользователю.
        :param user_id: ID пользователя.
        :param day: Дата установления квоты.
        :return: True, если запись успешно добавлена, иначе False.
        """
        return self.add(user_id=user_id, day=day)

    def get_actual_norm(self, actual_norm_id: int):
        """
        Получает информацию о квоте по её ID.
        :param actual_norm_id: ID актуальной нормы.
        :return: Найденная запись или None.
        """
        return self.get(actual_norm_id)

    def get_all_actual_norms(self):
        """
        Получает все квоты пользователей.
        :return: Список всех записей в таблице.
        """
        return self.all()

    def update_actual_norm(self, actual_norm_id: int, **kwargs) -> bool:
        """
        Обновляет данные квоты по её ID.
        :param actual_norm_id: ID квоты.
        :param kwargs: Поля и значения для обновления.
        :return: True, если запись успешно обновлена, иначе False.
        """
        return self.update(index=actual_norm_id, **kwargs)

    def delete_actual_norm(self, actual_norm_id: int) -> bool:
        """
        Удаляет квоту по её ID.
        :param actual_norm_id: ID квоты.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.delete(index=actual_norm_id)
