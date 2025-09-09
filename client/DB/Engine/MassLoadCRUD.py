from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from DB.Engine.BaseCRUD import BaseCRUD
from ..Models.MassLoad import MassLoad  # Импорт модели MassDrop


class EngineMassLoad(BaseCRUD):
    """
    Класс EngineMassLoad наследует от BaseCRUD и предоставляет интерфейс для работы с моделью MassLoad.
    Использует все методы из BaseCRUD для выполнения операций с таблицей MassLoad.
    """

    def __init__(self, session: Session):
        """
        Инициализация EngineMassLoad.

        :param session: Сессия SQLAlchemy для выполнения операций с базой данных.
        """
        # Инициализация родительского класса с переданными session и моделью MassLoad
        super().__init__(session, MassLoad)

    def add_mass_load(self, description: str, index: int) -> bool:
        """
        Добавляет новую задачу массовой загрузки.

        :param description: Описание задачи массовой загрузки.
        :param index: Индекс задачи.
        :return: True, если задача успешно добавлена, иначе False.
        """

        return self.add(id=index, description=description, created_at=datetime.now())
        # try:except IntegrityError as e:
        #     print(f"Ошибка добавления задачи массовой загрузки: {e}")
        #     return False

    def update_mass_load(self, mass_load_id: int, description: Optional[str] = None) -> bool:
        """
        Обновляет задачу массовой загрузки.

        :param mass_load_id: Уникальный идентификатор задачи.
        :param description: Новое описание задачи (опционально).
        :return: True, если обновление выполнено успешно, иначе False.
        """
        fields_to_update = {}
        if description is not None:
            fields_to_update['description'] = description
        return self.update(mass_load_id, **fields_to_update)

    def delete_mass_load(self, mass_load_id: int) -> bool:
        """
        Удаляет задачу массовой загрузки по её идентификатору.

        :param mass_load_id: Уникальный идентификатор задачи.
        :return: True, если задача успешно удалена, иначе False.
        """
        return self.delete(mass_load_id)

    def delete_all_mass_loads(self) -> bool:
        """
        Удаляет все задачи массовой загрузки из таблицы.

        :return: True, если таблица успешно очищена, иначе False.
        """

        return self.drop()  # Используем метод drop из BaseCRUD для удаления таблицы
            # try:except Exception as e:
            # print(f"Ошибка при удалении всех задач массовой загрузки: {e}")
            # return False

    def get_mass_load_by_id(self, mass_load_id: int) -> Optional[MassLoad]:
        """
        Возвращает задачу массовой загрузки по её идентификатору.

        :param mass_load_id: Уникальный идентификатор задачи.
        :return: Объект MassLoad или None, если задача не найдена.
        """
        return self.get(mass_load_id)
