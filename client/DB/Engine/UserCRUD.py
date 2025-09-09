from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from sqlalchemy import func
from .BaseCRUD import BaseCRUD  # Предполагается, что BaseCRUD уже реализован
from ..Models.User import User  # Импортируем связанные модели
from ..Models.Role import Role  # Импортируем связанные модели
from ..Models.History import History  # Импортируем связанные модели
from ..Models.Identification import Identification  # Импортируем связанные модели


class EngineUser(BaseCRUD):
    """
    Класс EngineUser предоставляет интерфейс для работы с таблицей User.
    Инкапсулирует логику CRUD операций и методы для взаимодействия с сущностью User.
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineUser.

        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
        super().__init__(session, User)

    def add_user(self,
                 index: int,
                 barcode: int,
                 code: int,
                 first_name: Optional[str],
                 second_name: Optional[str],
                 family: Optional[str],
                 password: Optional[str],
                 role_id: int) -> bool:
        """
        Добавляет нового пользователя в таблицу User.

        :param index: Уникальный идентификатор пользователя.
        :param barcode: Штрих-код пользователя.
        :param code: Код пользователя.
        :param first_name: Имя пользователя. (Необязательно)
        :param second_name: Фамилия пользователя. (Необязательно)
        :param family: Семейное положение или отчество пользователя. (Необязательно)
        :param password: Пароль пользователя. (Необязательно)
        :param role_id: Идентификатор роли пользователя.
        :return: True, если пользователь успешно добавлен, иначе False.

        **Примечание:**
        - Поле `barcode` и `code` являются обязательными и должны быть уникальными.
        - Поле `password` может быть пустым, если пользователь временно не имеет пароля.
        - Убедитесь, что идентификатор роли (`role_id`) существует в таблице `Role`, чтобы избежать нарушения ссылочной целостности.
        """

        return self.add(
            id=index,
            barcode=barcode,
            code=code,
            first_name=first_name,
            second_name=second_name,
            family=family,
            password=password,
            role_id=role_id
        )
        # try:except Exception as e:
        #     print(f"Error adding user: {e}")
        #     return False

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Получает пользователя по уникальному идентификатору.

        :param user_id: Уникальный идентификатор пользователя.
        :return: Объект User или None, если запись не найдена.
        """
        return self.get(user_id)
        # .session.query(User).options(joinedload(User.)).filter(User.id == user_id).one_or_none()

    def get_all_users(self, limit: int = 100):
        """
        Возвращает список всех пользователей с ограничением по количеству.

        :param limit: Максимальное количество пользователей для выборки.
        :return: Список объектов User.
        """
        return self.session.query(User).limit(limit).all()

    def update_user(self, user_id: int, **kwargs) -> bool:
        """
        Обновляет информацию о пользователе.

        :param user_id: Уникальный идентификатор пользователя.
        :param kwargs: Поля и их значения для обновления.
        :return: True, если обновление прошло успешно, иначе False.
        """
        return self.update(user_id, **kwargs)

    def delete_user(self, user_id: int) -> bool:
        """
        Удаляет пользователя по уникальному идентификатору.

        :param user_id: Уникальный идентификатор пользователя.
        :return: True, если пользователь успешно удален, иначе False.
        """
        return self.delete(user_id)

    def get_users_with_role(self, role_id: int):
        """
        Возвращает список пользователей, связанных с указанной ролью.

        :param role_id: Уникальный идентификатор роли.
        :return: Список объектов User.
        """
        return self.session.query(User).filter(User.role_id == role_id).all()

    def get_user_history(self, user_id: int) -> List[History]:
        """
        Возвращает список записей истории, связанных с пользователем.

        :param user_id: Уникальный идентификатор пользователя.
        :return: Список объектов History.
        """
        user = self.get_user_by_id(user_id)
        return user.stories if user else []

    def get_user_identifications(self, user_id: int) -> List[Identification]:
        """
        Возвращает список идентификаций, связанных с пользователем.

        :param user_id: Уникальный идентификатор пользователя.
        :return: Список объектов Identification.
        """
        user = self.get_user_by_id(user_id)
        return user.identifications if user else []

    def get_user_by_barcode(self, barcode: int) -> Optional[User]:
        """
        Получает пользователя по штрих-коду.

        :param barcode: Штрих-код пользователя.
        :return: Объект User или None, если пользователь не найден.

        **Примечание:**
        - Убедитесь, что штрих-код уникален для каждого пользователя, чтобы исключить дублирующие записи.
        """

        return self.session.query(User).filter(User.barcode == barcode).one_or_none()
            # try:except Exception as e:
            # print(f"Error retrieving user by barcode: {e}")
            # return None

    def get_user_by_code(self, code: int) -> Optional[User]:
        """
        Получает пользователя по коду.

        :param code: Код пользователя.
        :return: Объект User или None, если пользователь не найден.

        **Примечание:**
        - Убедитесь, что код уникален для каждого пользователя, чтобы исключить дублирующие записи.
        """

        return self.session.query(User).filter(User.code == code).one_or_none()
        # try:except Exception as e:
        #     print(f"Error retrieving user by code: {e}")
        #     return None

    def search_users_by_name(self, name_query: str):
        """
        Поиск пользователей по имени (имя или фамилия частично совпадает с запросом).

        :param name_query: Строка для поиска.
        :return: Список пользователей, соответствующих критериям поиска.
        """
        return self.session.query(User).filter(
            func.lower(User.first_name).like(f"%{name_query.lower()}%") |
            func.lower(User.second_name).like(f"%{name_query.lower()}%")
        ).all()

    def get_user_with_full_relationships(self, user_id: int) -> Optional[User]:
        """
        Получает пользователя с полным набором связанных данных (роль, истории, идентификации).

        :param user_id: Уникальный идентификатор пользователя.
        :return: Объект User или None.
        """
        return self.session.query(User).options(
            joinedload(User.role),
            joinedload(User.stories),
            joinedload(User.identifications)
        ).filter(User.id == user_id).one_or_none()
