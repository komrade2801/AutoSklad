from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Type
from DB.Engine.BaseCRUD import BaseCRUD
from DB.Models.History import History
from DB.Models.Role import Role
from DB.Models.User import User


class EngineRole(BaseCRUD):
    """
    Класс EngineRole предоставляет интерфейс для работы с таблицей Role.
    Инкапсулирует логику CRUD операций и предоставляет методы для работы с ролями, правами и связанными пользователями.
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineRole

        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных
        """
        super().__init__(session, Role)

    def add_role(self,
                 name: str,
                 description: Optional[str] = None,
                 parent_role_id: Optional[int] = None) -> bool:
        """
        Добавляет новую роль в таблицу Role.

        :param name: Название роли.
        :param description: Описание роли.
        :param parent_role_id: ID родительской роли.
        :return: True, если роль успешно добавлена, иначе False.
        """
        return self.add(name=name, description=description, parent_role_id=parent_role_id)

    def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """
        Получает роль по уникальному идентификатору.

        :param role_id: Уникальный идентификатор роли.
        :return: Объект Role или None, если запись не найдена.
        """
        return self.get(role_id)

    def get_roles_with_rights(self) -> list[Type[Role]]:
        """
        Возвращает список всех ролей с их правами доступа.

        :return: Список объектов Role со связанными правами доступа.
        """
        return self.session.query(Role).options(joinedload(Role.rights)).all()

    def update_role(self, role_id: int, name: Optional[str] = None, description: Optional[str] = None,
                    parent_role_id: Optional[int] = None) -> bool:
        """
        Обновляет информацию о роли.

        :param role_id: Уникальный идентификатор роли.
        :param name: Новое название роли.
        :param description: Новое описание роли.
        :param parent_role_id: Новый ID родительской роли.
        :return: True, если роль успешно обновлена, иначе False.
        """
        updates = {}
        if name is not None:
            updates['name'] = name
        if description is not None:
            updates['description'] = description
        if parent_role_id is not None:
            updates['parent_role_id'] = parent_role_id
        return self.update(role_id, **updates)

    def delete_role(self, role_id: int) -> bool:
        """
        Удаляет роль по её уникальному идентификатору.

        :param role_id: Уникальный идентификатор роли.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.delete(role_id)

    def get_users_with_role(self, role_id: int) -> List[User]:
        """
        Возвращает список пользователей, связанных с указанной ролью.

        :param role_id: Уникальный идентификатор роли.
        :return: Список объектов User, связанных с ролью.
        """
        role = self.get_role_by_id(role_id)
        return role.users if role else []

    def get_history_by_role(self, role_id: int) -> List[History]:
        """
        Возвращает историю, связанную с указанной ролью.

        :param role_id: Уникальный идентификатор роли.
        :return: Список объектов History, связанных с ролью.
        """
        role = self.get_role_by_id(role_id)
        return role.stories if role else []

    def get_child_roles(self, role_id: int) -> List[Role]:
        """
        Возвращает список дочерних ролей для указанной роли.

        :param role_id: Уникальный идентификатор родительской роли.
        :return: Список объектов Role, являющихся дочерними для данной роли.
        """
        role = self.get_role_by_id(role_id)
        return role.child_roles if role else []

    def get_parent_role(self, role_id: int) -> Optional[Role]:
        """
        Возвращает родительскую роль для указанной роли.

        :param role_id: Уникальный идентификатор роли.
        :return: Объект Role, являющийся родительской ролью, или None.
        """
        role = self.get_role_by_id(role_id)
        return role.parent_role if role else None

    def get_all_roles(self) -> List[Role]:
        """
        Возвращает список всех ролей в таблице Role.

        :return: Список всех ролей.
        """
        return self.all()
