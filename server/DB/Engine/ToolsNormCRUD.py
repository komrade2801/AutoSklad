from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.ToolsNorm import ToolsNorm


class EngineToolsNorm(BaseCRUD):
    """
    Класс EngineToolsNorm предоставляет интерфейс для работы с таблицей ToolsNorm.
    Инкапсулирует CRUD-операции и обеспечивает удобные методы для работы с нормами для инструментов.
    """

    def __init__(self, session: Session=None):        
        """        Инициализация класса EngineToolsNorm.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
                
        super().__init__(session=session, model=ToolsNorm)

    def add_tools_norm(self, tools_id: int, actual_norm_id: int, summa: int = None, summa_of_periods: int = None,
                       type_periods: str = None, summa_of_use: str = None, start_date=None, description: str = None) -> bool:
        """
        Добавляет новую норму для инструмента.

        :param tools_id: ID инструмента.
        :param actual_norm_id: ID актуальной нормы.
        :param summa: Сумма нормы.
        :param summa_of_periods: Количество периодов.
        :param type_periods: Тип периодов (например, "День").
        :param summa_of_use: Сумма использования.
        :param start_date: Дата начала действия нормы (datetime или строка в формате ISO).
        :param description: Дополнительное описание.
        :return: True, если запись успешно добавлена, иначе False.
        """
        return self.add(
            tools_id=tools_id,
            actual_norm_id=actual_norm_id,
            summa=summa,
            summa_of_periods=summa_of_periods,
            type_periods=type_periods,
            summa_of_use=summa_of_use,
            start_date=start_date,
            description=description
        )

    def get_tools_norm(self, tools_norm_id: int):
        """
        Получает информацию о норме инструмента по его ID.

        :param tools_norm_id: ID нормы.
        :return: Найденная запись или None.
        """
        return self.get(tools_norm_id)

    def get_all_tools_norms(self):
        """
        Получает все нормы для инструментов.

        :return: Список всех записей в таблице.
        """
        return self.all()

    def update_tools_norm(self, tools_norm_id: int, **kwargs) -> bool:
        """
        Обновляет данные нормы инструмента по его ID.

        :param tools_norm_id: ID нормы.
        :param kwargs: Поля и значения для обновления.
        :return: True, если запись успешно обновлена, иначе False.
        """
        return self.update(tools_norm_id, **kwargs)

    def delete_tools_norm(self, tools_norm_id: int) -> bool:
        """
        Удаляет норму инструмента по его ID.

        :param tools_norm_id: ID нормы.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.delete(index=tools_norm_id)

    def get_tools_norm_by_tool_id(self, tool_id: int):
        """
        Получает список норм для инструмента, связанных с указанным инструментом.

        :param tool_id: ID инструмента.
        :return: Список объектов ToolsNorm, связанных с данным инструментом.
        """
        return self.session.query(ToolsNorm).filter_by(tools_id=tool_id).all()
