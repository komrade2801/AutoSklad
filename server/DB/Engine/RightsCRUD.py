from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
# from datetime import datetime

from DB.Engine.CRUD import BaseCRUD
from DB.Models.Rights import Rights
from DB.Models.Role import Role
# from DB.Models.Page import Page


class EngineRights(BaseCRUD):
    """
    Класс EngineRights предоставляет интерфейс для работы с таблицей Rights.
    Инкапсулирует логику CRUD операций и дополнительные методы для работы с правами доступа.
    """

    def __init__(self, session: Session=None):        
        """        Инициализация EngineRights.
        :param session: Объект сессии SQLAlchemy для операций с БД.
        """
                
        super().__init__(session=session, model=Rights)

    def add_right(
            self,
            index:int,
            name: str,
            role_id: int,
            page_id: int,
            description: Optional[str] = None
    ) -> bool:
        """
        Добавляет новое право доступа.

        :param index:
        :param name: Название права.
        :param role_id: ID роли.
        :param page_id: ID страницы.
        :param description: Описание (опционально).
        :return: True, если успешно добавлено.
        """
        return self.add(
            index=index,
            name=name,
            role_id=role_id,
            page_id=page_id,
            description=description
        )

    def get_right_by_id(self, right_id: int) -> Optional[Rights]:
        """
        Получает право по его ID.

        :param right_id: Уникальный идентификатор.
        :return: Объект Rights или None.
        """
        return self.get(index=right_id)

    def get_rights_by_role(self, role_id: int) -> List[Rights]:
        """
        Возвращает все права для данной роли.

        :param role_id: ID роли.
        :return: Список объектов Rights.
        """
        # вместо прямого session.query… — просто:
        return self.get_by_role_id(role_id)

    def get_rights_by_page(self, page_id: int) -> List[Rights]:
        """
        Возвращает все права для данной страницы.

        :param page_id: ID страницы.
        :return: Список объектов Rights.
        """
        return self.get_by_page_id(index=page_id)

    def update_right(
            self,
            right_id: int,
            name: Optional[str] = None,
            role_id: Optional[int] = None,
            page_id: Optional[int] = None,
            description: Optional[str] = None
    ) -> bool:

        """
        Обновляет поля права доступа.
        :param right_id: ID права.
        :param name: Новое название.
        :param role_id: Новый ID роли.
        :param page_id: Новый ID страницы.
        :param description: Новое описание.
        :return: True, если обновлено.
        """

        updates = {}
        if name is not None:
            updates["Name"] = name
        if role_id is not None:
            updates["role_id"] = role_id
        if page_id is not None:
            updates["page_id"] = page_id
        if description is not None:
            updates["description"] = description
        return self.update(index=right_id, **updates)

    def delete_right(self, right_id: int) -> bool:
        """
        Удаляет право по его ID.

        :param right_id: ID удаляемого права.
        :return: True, если удалено.
        """
        return self.delete(index=right_id)

    def get_all_rights(self) -> List[Rights]:
        """
        Возвращает все записи таблицы Rights.

        :return: Список всех прав.
        """
        return self.all()


    def get_rights_with_relations(self) -> List[Rights]:
        """
        Возвращает все права с загруженными объектами Role и Page.
        """
        # используем joinedload для жадной загрузки связей
        return self.with_options(
            joinedload(self.model.role),   # assuming relationship property is `role`
            joinedload(self.model.page)    # and `page`
        )

    def search_rights(self, name_substring: str) -> List[Rights]:
        """
        Ищет права по части названия.
        """
        return self.filter(
            self.model.name.ilike(f"%{name_substring}%")
        )

    def get_rights_by_role_id(self, role_id: int) -> List[Rights]:
        """
        Возвращает права, связанные с определённой ролью, через join.
        """
        return self.join_and_filter(
            [Role],
            Role.id == self.model.role_id,
            Role.id == role_id
        )
