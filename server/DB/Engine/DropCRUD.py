import datetime

from sqlalchemy.orm import Session
from typing import List, Optional

from .CRUD import BaseCRUD  # Импорт вашего BaseCRUD
from DB.Models.Drop import Drop  # Импортируем модель Cell


class EngineDrop(BaseCRUD):
    """
    Класс EngineDrop предоставляет удобный интерфейс для работы с моделью Drop,
    используя функционал базового класса BaseCRUD.

    Основные функции:
    - Получение всех записей Drop.
    - Получение записи по ID.
    - Добавление новой записи.
    - Обновление существующей записи.
    - Удаление записи.
    - Поиск по полям: tools_id, mass_drop_id, cell_id.
    """

    def __init__(self, session: Session=None):
        """
        Инициализация класса EngineDrop.

        :param session: Объект сессии SQLAlchemy для работы с базой данных.
        """
                
        super().__init__(session=session, model=Drop)

    def get_drop_by_id(self, drop_id: int) -> Optional[Drop]:
        """
        Получает ячейку по её уникальному идентификатору.

        :param drop_id: Уникальный идентификатор ячейки.
        :return: Объект Cell или None, если запись не найдена.
        """
        return self.get(drop_id)

    def get_by_tools_id(self, tools_id: int) -> List[Drop]:
        """
        Получает все записи Drop, связанные с указанным tools_id.

        :param tools_id: Идентификатор инструмента.
        :return: Список объектов Drop.
        """
        return self.session.query(self.model).filter_by(tools_id=tools_id).all()

    def get_by_mass_drop_id(self, mass_drop_id: int) -> List[Drop]:
        """
        Получает все записи Drop, связанные с указанным mass_drop_id.

        :param mass_drop_id: Идентификатор массовой выдачи.
        :return: Список объектов Drop.
        """
        return self.session.query(self.model).filter_by(mass_drop_id=mass_drop_id).all()

    def get_by_cell_id(self, cell_id: int) -> List[Drop]:
        """
        Получает все записи Drop, связанные с указанным cell_id.
        :param cell_id: Идентификатор ячейки.
        :return: Список объектов Drop.
        """
        return self.session.query(self.model).filter_by(cell_id=cell_id).all()

    def add_drop(self,
                index: int,
                created_at: datetime.date,
                cell_id: int,
                mass_drop_id: int,
                tools_id: int,
                history_id: int,
                 status_id: int,
                plan_id: Optional[int] = None,
                description: Optional[str] = None,
        ) -> bool:
        """
        Добавляет новую запись в таблицу Drop.
        :param created_at:
        :param index:
        :param tools_id: Идентификатор инструмента.
        :param mass_drop_id: Идентификатор массовой выдачи.
        :param cell_id: Идентификатор ячейки.
        :param description: Описание операции.
        :return: True если запись успешно добавлена, иначе False.
        """
        return self.add(
            index=index,
            description=description,
            created_at=created_at,
            cell_id=cell_id,
            mass_drop_id=mass_drop_id,
            tools_id=tools_id,
            status_id=status_id,
            plan_id=plan_id,
            history_id=history_id
        )

    def update_drop(self,
            drop_id: int,
            **kwargs
        ) -> bool:
        """
        Обновляет существующую запись Drop.

        :param drop_id: Уникальный идентификатор записи.
        :param kwargs: Поля и значения для обновления.
        :return: True если запись успешно обновлена, иначе False.
        """
        return self.update(drop_id, **kwargs)

    def delete_drop(self, drop_id: int) -> bool:
        """
        Удаляет запись Drop по ID.

        :param drop_id: Уникальный идентификатор записи.
        :return: True если запись успешно удалена, иначе False.
        """
        return self.delete(index=drop_id)

    def create_drop(self, write_off_data) -> bool:
        """
        Создает новую запись Drop на основе переданных данных.

        :param write_off_data: Словарь с данными для создания записи.
            Ожидаемые ключи: tools_id, mass_drop_id, cell_id, description (опционально).
        :return: True если запись успешно создана, иначе False.
        """
        required_fields = {"tools_id", "mass_drop_id", "cell_id"}
        if not required_fields.issubset(write_off_data):
            raise ValueError(f"Отсутствуют обязательные поля: {required_fields - set(write_off_data)}")

        return self.add(
            tools_id=write_off_data["tools_id"],
            mass_drop_id=write_off_data["mass_drop_id"],
            cell_id=write_off_data["cell_id"],
            description=write_off_data.get("description")
        )


    def get_drops_by_tool_ids(self, tool_ids: List[int]):
        """
        Получает все записи Drop, связанные с указанными tools_id.

        :param tool_ids: Список идентификаторов инструментов.
        :return: Список объектов Drop.
        """
        return self.session.query(Drop).filter(Drop.tools_id.in_(tool_ids)).all()

    def find_by_tools_id_and_status_list(self, tools_id: int, status_id_list: List[int]) -> List[Drop]:
        """
        Возвращает список записей Load, связанных с указанным tools_id.
        """
        return self.session.query(self.model).filter_by(tools_id=tools_id).filter(self.model.status_id.in_(status_id_list)).all()

    def update_drop_from_data(self, drop_id, write_off_data):
        pass

