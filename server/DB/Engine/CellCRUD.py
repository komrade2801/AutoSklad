from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from API.backend.request_models import CellUpdate
# , Type
from DB.Engine.CRUD import BaseCRUD
from DB.Models.Cell import Cell


class EngineCell(BaseCRUD):
    """
    Класс EngineCell предоставляет интерфейс для работы с таблицей Cell.
    Инкапсулирует CRUD-операции и предоставляет методы для работы с ячейками, их группами и инструментами.
    """

    def __init__(self, session: Session = None):
        """
        Инициализация класса EngineCell.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
        # Передаем модель Cell и сессию в BaseCRUD.

        super().__init__(session=session, model=Cell)

    def add_cell(self,
                 index: int,
                 number: int,
                 status_id: int,
                 tools_id: Optional[int] = None,
                 groups_id: Optional[int] = None,
                 description: Optional[str] = None
                 ) -> bool:
        """
        Добавляет новую ячейку в таблицу Cell.
        Интерфейс функции не меняется, но теперь не передаём параметр id,
        чтобы база данных сама генерировала уникальный идентификатор.
        """
        return self.add(
            index=index,
            number=number,
            groups_id=groups_id,
            tools_id=tools_id,
            description=description,
            status_id=status_id
        )

    def get_cell_by_id(self, cell_id: int) -> Optional[Cell]:
        """
        Получает ячейку по её уникальному идентификатору.
        """
        return self.get(cell_id)

    def get_cells_with_groups_and_tools(self) -> List[Cell]:
        """
        Возвращает список всех ячеек с загруженными группами и инструментами.
        Используется joinedload для предварительной загрузки отношений.
        """
        return (
            self.session.query(Cell)
            .options(joinedload("Groups"), joinedload("Tools"))
            .all()
        )

    # def update_cell(self,cell_id : int,
    #                 number,
    #                 description,
    #                 groups_id,
    #                 tools_id,
    #                 status_id,
    # ) -> bool:
    #     """
    #     Обновляет параметры ячейки по её уникальному идентификатору.
    #     """
    #     return self.update(
    #         index=cell_id,
    #         number=number,
    #         description=description,
    #         groups_id=groups_id,
    #         tools_id=tools_id,
    #         status_id=status_id,
    #     )

    def update_cell(self, cell_id: int,
                    number=None,
                    description=None,
                    groups_id=None,
                    tools_id=None,
                    status_id=None,
                    ) -> bool:
        """
            Обновляет параметры ячейки по её уникальному идентификатору.
            :param status_id:
            :param tools_id:
            :param groups_id:
            :param description:
            :param number:
            :param cell_id: Уникальный идентификатор ячейки.
            :return: True, если запись успешно обновлена, иначе False.
        """
        print(f"update_cell {cell_id}, {number}, {description}, {groups_id}, {tools_id}, {status_id}")

        # 1) Загружаем из БД текущее состояние
        instance = self.session.query(self.model).get(cell_id)
        if not instance:
            return False

        # 2) Собираем поля для обновления
        # Для массовой загрузки важно всегда создавать команды синхронизации,
        # даже если значения не изменились, поэтому добавляем все переданные поля
        updates = {}
        if number is not None:
            updates['number'] = number
        if description is not None:
            updates['description'] = description
        # Для массовой загрузки всегда добавляем groups_id, tools_id, status_id,
        # чтобы гарантировать создание команды синхронизации
        if groups_id is not None:
            updates['groups_id'] = groups_id
        if tools_id is not None:
            updates['tools_id'] = tools_id
        if status_id is not None:
            updates['status_id'] = status_id

        # 3) Если нечего менять — вернём True, потому что ошибок нет
        if not updates:
            return True

        # 4) Всегда вызываем update для создания команды синхронизации
        # @sync_aware декоратор гарантирует создание команды, даже если значения не изменились
        print(f"[update_cell] Вызов self.update для cell_id={cell_id}, "
              f"updates={updates}, device_id={getattr(self, 'device_id', 'NOT SET')}")
        result = self.update(index=cell_id, **updates)
        print(f"[update_cell] Результат self.update: {result}")
        return result

    def delete_cell(self, cell_id: int) -> bool:
        """
        Удаляет ячейку по её уникальному идентификатору.
        """
        return self.delete(index=cell_id)

    def get_cells_by_group(self, group_id: int) -> List[Cell]:
        """
        Возвращает список всех ячеек, принадлежащих указанной группе.
        """
        return self.session.query(Cell).filter(Cell.groups_id == group_id).all()

    def get_cells_by_tool(self, tool_id: int) -> List[Cell]:
        """
        Возвращает список всех ячеек, связанных с указанным инструментом.
        """
        return self.session.query(Cell).filter(Cell.tools_id == tool_id).all()

    def get_all_cells(self) -> List[Cell]:
        """
        Возвращает список всех ячеек в таблице Cell.
        """
        return self.all()

    def get_all_empty_cells(self) -> List[Cell]:
        """
        Возвращает список всех пустых ячеек в таблице Cell.
        """
        return self.session.query(Cell).filter(Cell.tools_id == None).all()

    def get_cells_by_description(self, description: str) -> List[Cell]:
        """
        Возвращает список ячеек, соответствующих указанному описанию.
        """
        return self.session.query(Cell).filter(Cell.description == description).all()

    def update_cell_status(self, cell_id: int, status_id: int) -> bool:
        """
        Обновляет статус ячейки по её уникальному идентификатору.
        """
        return self.update(cell_id, status_id=status_id)

    def get_cell_by_tool_id(self, tool_id: int) -> Optional[Cell]:
        """
        Получает первую найденную ячейку, связанную с указанным инструментом.
        """
        return self.session.query(Cell).filter(Cell.tools_id == tool_id).first()

    def get_cell_by_number(self, cell_number: int) -> Optional[Cell]:
        """
        Получает ячейку по её номеру.
        """
        return self.session.query(Cell).filter(Cell.number == cell_number).first()

    def create_cell(self,
                    index: int,
                    number: int,
                    tools_id: int,
                    status_id: int,
                    groups_id: Optional[int] = None,
                    description: Optional[str] = None
                    ) -> Optional[Cell]:
        """
        Создаёт новую ячейку с заданным номером и описанием.
        Генерирование нового уникального идентификатора происходит через автогенерацию БД.
        """
        if self.add_cell(index, number, tools_id, status_id, groups_id, description):
            return self.session.query(Cell).filter_by(number=number).first()
        return None

    def get_cells_by_ids(self, cell_ids: List[int]) -> List[Cell]:
        """
        Возвращает список ячеек по списку идентификаторов.
        """
        return self.session.query(Cell).filter(Cell.id.in_(cell_ids)).all()

    def update_cell_from_data(self, cell_id: int, cell_data: CellUpdate) -> bool:
        """
        Обновляет ячейку по переданным данным.
        Обновляются только те поля, которые присутствуют в объекте модели.
        """
        cell = self.get_cell_by_id(cell_id)
        if not cell:
            return False
        update_data = {k: v for k, v in cell_data.items() if hasattr(cell, k)}
        return self.update(cell_id, **update_data)
