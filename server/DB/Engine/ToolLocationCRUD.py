from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
# from DB.Models import ToolLocation
from DB.Models.ToolLocation import ToolLocation


class EngineToolLocation(BaseCRUD):
    """
    Класс EngineToolLocation предоставляет интерфейс для работы с таблицей ToolLocation.
    Инкапсулирует CRUD-операции и обеспечивает удобные методы для работы с привязками инструментов к их статусам.
    """

    def __init__(self, session: Session=None):        
        """        Инициализация класса EngineToolLocation.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
                
        super().__init__(session=session, model=ToolLocation)

    def add_link(self, tools_id: int, status_id: int) -> bool:
        """
        Добавляет связь между инструментом и его статусом.
        :param tools_id: ID инструмента.
        :param status_id: ID статуса.
        :return: True, если запись успешно добавлена, иначе False.
        """
        return self.add(tools_id=tools_id, status_id=status_id)

    def get_link(self, tools_id: int):
        """
        Получает статус инструмента по его ID.
        :param tools_id: ID инструмента.
        :return: Найденная запись или None.
        """
        return self.session.query(self.model).filter_by(tools_id=tools_id).first()

    def get_all_links(self):
        """
        Получает все связи инструментов с их статусами.
        :return: Список всех записей в таблице.
        """
        return self.all()

    # def update_status(self, tools_id: int, status_id: int):
    #     return self.update(tools_id, status_id=status_id)

    def delete_link(self, tools_id: int):
        """
        Удаляет связь между инструментом и статусом.
        :param tools_id: ID инструмента.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.session.query(self.model).filter_by(tools_id=tools_id).delete()

    def update_status(self, tools_id: int, status_id: int) -> bool:
        """
        Обновляет статус инструмента.
        :param tools_id: ID инструмента.
        :param status_id: Новый ID статуса.
        :return: True, если запись успешно обновлена, иначе False.
        """

        location = self.session.query(ToolLocation).filter(ToolLocation.tools_id == tools_id).first()
        if location:
            location.status_id = status_id
            self.session.commit()
            return True
        return False