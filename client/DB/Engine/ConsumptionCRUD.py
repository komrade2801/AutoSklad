from sqlalchemy.orm import Session
from typing import List, Optional
from .BaseCRUD import BaseCRUD
from DB.Models.Consumption import Consumption  # Импортируем модель Cell


class EngineConsumption(BaseCRUD):
    """
    Класс EngineConsumption предоставляет высокоуровневый интерфейс для работы с таблицей Consumption.
    Наследуется от BaseCRUD, добавляя дополнительные методы для обработки данных о расходе инструментов.
    """

    def __init__(self, session: Session = None):
        """
        Инициализация класса EngineConsumption.

        :param session: Объект сессии SQLAlchemy для работы с базой данных.
        """

        super().__init__(session=session, model=Consumption)

    def add_consumption(self,
                        index: int,
                        cells_id: int,
                        tool_id: int,
                        plan_id: int,
                        history_id: int) -> bool:
        """
        Получает ячейку по её уникальному идентификатору.

        :param tool_id:
        :param cells_id:
        :param index: Уникальный идентификатор ячейки.
        :return: Объект Cell или None, если запись не найдена.
        """
        return self.add(
            index=index,
            cell_id=cells_id,
            tools_id=tool_id,
            plan_id=plan_id,
            history_id=history_id)

    def get_consumption_by_id(self, consumption_id: int) -> Optional[Consumption]:
        """
        Получает ячейку по её уникальному идентификатору.

        :param consumption_id: Уникальный идентификатор ячейки.
        :return: Объект Cell или None, если запись не найдена.
        """
        return self.get(consumption_id)

    def get_by_tool_id(self, tools_id: int) -> List[Consumption]:
        """
        Получает список записей расхода по идентификатору инструмента.

        :param tools_id: Идентификатор инструмента.
        :return: Список объектов Consumption, связанных с указанным инструментом.
        """
        return self.session.query(self.model).filter_by(tools_id=tools_id).all()

    def get_by_cell_id(self, cell_id: int) -> List[Consumption]:
        """
        Получает список записей расхода по идентификатору ячейки.

        :param cell_id: Идентификатор ячейки.
        :return: Список объектов Consumption, связанных с указанной ячейкой.
        """
        return self.session.query(self.model).filter_by(cell_id=cell_id).all()

    # def get_recent(self, limit: int = 10) -> List[Consumption]:
    #     """
    #     Получает последние записи расхода.
    #
    #     :param limit: Максимальное количество записей для возврата.
    #     :return: Список объектов Consumption.
    #     """
    #     return self.session.query(self.model).order_by(self.model.created_at.desc()).limit(limit).all()

    def update_consumption(self,
                            consumption_id: int,
                            cell_id: int,
                            tools_id: int,
                            plan_id: int,
                            history_id: int) -> bool:
        """
        Обновляет записи расхода.

        :param tools_id:
        :param consumption_id: Уникальный идентификатор записи расхода.
        :param cell_id: Новый комментарий.
        :return: True если обновление прошло успешно, иначе False.
        """
        return self.update(
            index=consumption_id,
            cell_id=cell_id,
            tools_id=tools_id,
            plan_id=plan_id,
            history_id=history_id,
        )

    def delete_by_tool_id(self, tools_id: int) -> int:
        """
        Удаляет все записи расхода для указанного инструмента.

        :param tools_id: Идентификатор инструмента.
        :return: Количество удаленных записей.
        """
        rows_deleted = self.session.query(self.model).filter_by(tools_id=tools_id).delete()

        self.session.commit()
        # try:except Exception:
        #     self.session.rollback()
        #     raise
        return rows_deleted
