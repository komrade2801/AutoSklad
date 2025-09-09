from sqlalchemy.orm import Session
from typing import Optional
# from sqlalchemy.exc import IntegrityError
from datetime import datetime
from DB.Engine.CRUD import BaseCRUD  # Импортируем BaseCRUD
from DB.Models.Help import Help  # Импортируем модель Help


class EngineHelp(BaseCRUD):
    """
    Класс EngineHelp предоставляет удобный интерфейс для работы с таблицей Help в базе данных
    Он инкапсулирует логику CRUD операций и предоставляет дополнительные методы, специфичные для Help
    """

    def __init__(self, session: Session=None):        
        """        Инициализация класса EngineHelp

        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных
        """
        
        super().__init__(session=session, model=Help)

    def add_help_entry(self, text: str, data: Optional[datetime] = None) -> bool:
        """
        Добавляет новую запись в таблицу Help

        :param text: Текст записи.
        :param data: Дата записи. Если не указана, используется текущая дата и время.
        :return: True если запись успешно добавлена, иначе False.
        """
        if data is None:
            data = datetime.utcnow()  # Устанавливаем текущую дату и время, если не указано

        return self.add(text=text, data=data)

    def get_help_by_id(self, help_id: int) -> Optional[Help]:
        """
        Получает запись из таблицы Help по уникальному идентификатору.

        :param help_id: Уникальный идентификатор записи.
        :return: Объект Help или None, если запись не найдена.
        """
        return self.get(help_id)

    def update_help_entry(self, help_id: int, text: Optional[str] = None, data: Optional[datetime] = None) -> bool:
        """
        Обновляет запись в таблице Help по уникальному идентификатору.

        :param help_id: Уникальный идентификатор записи.
        :param text: Новый текст записи.
        :param data: Новая дата записи.
        :return: True если запись успешно обновлена, иначе False.
        """
        updates = {}
        if text is not None:
            updates["text"] = text
        if data is not None:
            updates["data"] = data
        return self.update(help_id, **updates)

    def delete_help_entry(self, help_id: int) -> bool:
        """
        Удаляет запись из таблицы Help по уникальному идентификатору.

        :param help_id: Уникальный идентификатор записи.
        :return: True если запись успешно удалена, иначе False.
        """
        return self.delete(index=help_id)

    def get_all_help_entries(self):
        """
        Получает все записи из таблицы Help.

        :return: Список всех записей таблицы Help.
        """
        return self.all()
