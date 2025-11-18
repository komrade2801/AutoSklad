from sqlalchemy.orm import Session
from typing import Optional, List
from DB.Engine.CRUD import BaseCRUD
from ..Models.Load import Load  # Импорт модели Load


class EngineLoad(BaseCRUD):
    """
    Класс EngineLoad предоставляет интерфейс для работы с моделью Load.
    Наследуется от BaseCRUD, при этом не использует прямые session.query.
    """

    def __init__(self, session: Session = None):
        """        Инициализация класса EngineLoad.

        :param session: Объект сессии SQLAlchemy для работы с базой данных.
        """

        super().__init__(session=session, model=Load)

    def add_load(self,
                 load_id: int,
                 description: str,
                 tools_id: int,
                 mass_load_id: int,
                 cell_id: int,
                 plan_id: int,
                 history_id: int) -> bool:
        """
        Добавляет новую запись о загрузке инструментов в базу данных.
        """
        return self.add(
            index=load_id,
            description=description,
            tools_id=tools_id,
            mass_load_id=mass_load_id,
            cell_id=cell_id,
            plan_id=plan_id,
            history_id=history_id
        )

    def get_load_by_id(self, load_id: int) -> Optional[Load]:
        """
        Получает запись Load по её ID.
        """
        return self.get(load_id)

    def find_by_tools_id(self, tools_id: int) -> List[Load]:
        """
        Возвращает список записей Load, связанных с указанным tools_id.
        """
        return self.get_by_tools_id(tools_id)

    def find_by_cell_id(self, cell_id: int) -> List[Load]:
        """
        Возвращает список записей Load, связанных с указанным tools_id.
        """
        return self.session.query(Load).filter(Load.cell_id == cell_id).all()

    def find_by_plan_id(self, plan_id: int) -> List[Load]:
        """
        Возвращает список записей Load, связанных с указанным plan_id.
        """
        return self.session.query(Load).filter(Load.plan_id == plan_id).all()

    def find_by_mass_load_id(self, mass_load_id: int) -> List[Load]:
        """
        Возвращает список записей Load, связанных с указанным mass_load_id.
        """
        return self.get_by_mass_load_id(mass_load_id)

    def update_description(self, load_id: int, description: str) -> bool:
        """
        Обновляет описание для записи Load по указанному идентификатору.
        """
        return self.update(load_id, description=description)

    def delete_by_tools_id(self, tools_id: int) -> int:
        """
        Удаляет все записи Load, связанные с указанным tools_id.
        :return: Количество удаленных записей.
        """
        # Получаем все записи и удаляем по одной
        records = self.get_by_tools_id(tools_id)
        count = 0
        for rec in records:
            # BaseCRUD.delete принимает PK id,
            # но здесь PK — это просто id поля модели Load
            self.delete(index=rec.id)
            count += 1
        return count

    def count_by_cell_id(self, cell_id: int) -> int:
        """
        Возвращает количество записей Load, связанных с указанным cell_id.
        """
        # filter_by возвращает список, считаем его длину
        return len(self.filter_by(cell_id=cell_id))

    def get_loads_by_mass_load_id(self, mass_load_id: int):  # -> List[Load]
        """
        Возвращает список всех записей Load, связанных с указанным mass_load_id.

        :param mass_load_id: Идентификатор массовой загрузки.
        :return: Список объектов Load.
        """
        return self.filter_by(mass_load_id=mass_load_id)