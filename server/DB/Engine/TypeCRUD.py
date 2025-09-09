from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.Type import Type


class EngineType(BaseCRUD):
    """
    Класс EngineType предоставляет интерфейс для работы с таблицей Type.
    Инкапсулирует CRUD-операции и обеспечивает удобные методы для работы с типами операций.
    """

    def __init__(self, session: Session=None):        
        """        Инициализация класса EngineType.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
                
        super().__init__(session=session, model=Type)

    def add_type(self, name: str, operation: str) -> bool:
        """
        Добавляет новый тип операции.
        :param name: Название типа.
        :param operation: Описание операции.
        :return: True, если запись успешно добавлена, иначе False.
        """
        return self.add(name=name, operation=operation)

    def get_type(self, type_id: int):
        """
        Получает информацию о типе по его ID.
        :param type_id: ID типа.
        :return: Найденная запись или None.
        """
        return self.get(type_id)

    def get_all_types(self) -> list[Type]:
        """
        Получает все типы операций.
        :return: Список всех записей в таблице.
        """
        return self.all()

    def update_type(self, type_id: int,
                    name: str,
                    operation: str
                    ) -> bool:
        """
        Обновляет данные типа по его ID.
        :param operation:
        :param name:
        :param type_id: ID типа.
        :return: True, если запись успешно обновлена, иначе False.
        """
        return self.update(index=type_id,
                           name=name,
                           operation=operation
                           )

    def delete_type(self, type_id: int) -> bool:
        """
        Удаляет тип по его ID.
        :param type_id: ID типа.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.delete(index=type_id)
