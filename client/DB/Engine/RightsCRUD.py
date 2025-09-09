from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from .BaseCRUD import BaseCRUD  # Предполагается, что BaseCRUD уже реализован
from ..Models.Role import Role
from ..Models.Rights import Rights   # Импорт модели Rights


class EngineRights(BaseCRUD):
    """
    Класс EngineRights предоставляет интерфейс для работы с таблицей Rights.
    Инкапсулирует логику CRUD операций и предоставляет методы для работы с правами доступа.
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineRights.

        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
        super().__init__(session, Rights)

    def add_right(self,
                  index: int,
                  name: str,
                  description: Optional[str],
                  role_id: int) -> bool:
        """
        Добавляет новое право доступа в таблицу Rights.

        :param index:
        :param name: Название права доступа.
        :param description: Описание права доступа (необязательное поле).
        :param role_id: Идентификатор роли, к которой привязано право.
        :return: True, если запись успешно добавлена, иначе False.
        """
        return self.add(id=index, name=name, description=description, role_id=role_id)

    def get_right_by_id(self, right_id: int) -> Optional[Rights]:
        """
        Получает право доступа по уникальному идентификатору.

        :param right_id: Уникальный идентификатор права доступа.
        :return: Объект Rights или None, если запись не найдена.
        """
        return self.get(right_id)

    def get_rights_by_role_id(self, role_id: int) -> List[Rights]:
        """
        Возвращает все права доступа, связанные с определенной ролью.

        :param role_id: Идентификатор роли.
        :return: Список объектов Rights.
        """
        return self.session.query(self.model).filter_by(role_id=role_id).all()

    def update_right(self, right_id: int, name: Optional[str] = None, description: Optional[str] = None, role_id: Optional[int] = None) -> bool:
        """
        Обновляет право доступа по его уникальному идентификатору.

        :param right_id: Уникальный идентификатор права доступа.
        :param name: Новое название права доступа (опционально).
        :param description: Новое описание права доступа (опционально).
        :param role_id: Новый идентификатор роли (опционально).
        :return: True, если запись успешно обновлена, иначе False.
        """
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if role_id is not None:
            update_data["role_id"] = role_id
        return self.update(right_id, **update_data)

    def delete_right(self, right_id: int) -> bool:
        """
        Удаляет право доступа по его уникальному идентификатору.

        :param right_id: Уникальный идентификатор права доступа.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.delete(right_id)

    def get_all_rights(self) -> List[Rights]:
        """
        Возвращает список всех прав доступа в таблице Rights.

        :return: Список всех прав доступа.
        """
        return self.all()

    def get_rights_with_role(self) -> List[Rights]:
        """
        Возвращает список прав доступа с загруженными данными о роли.

        :return: Список объектов Rights с предзагруженными связанными объектами Role.
        """
        # Выполняем JOIN запрос, чтобы получить данные о правах и связанных ролях
        results = (
            self.session.query(self.model, Role)
            .join(Role, Role.id == self.model.role_id)  # Связываем таблицу прав с таблицей ролей
            .all()  # Получаем все результаты
        )

        # Формируем список объектов Rights с данными о роли
        rights_with_roles = []
        for right, role in results:
            # Создаем объект Rights и добавляем информацию о роли
            right.role = role  # Устанавливаем роль в объект права
            rights_with_roles.append(right)  # Добавляем в итоговый список

        return rights_with_roles

    def search_rights(self, name_substring: str) -> List[Rights]:
        """
        Выполняет поиск прав доступа по подстроке в названии.

        :param name_substring: Подстрока для поиска.
        :return: Список объектов Rights, соответствующих критерию поиска.
        """
        return self.session.query(self.model).filter(Rights.name.like(f"%{name_substring}%")).all()
