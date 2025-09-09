from sqlalchemy.orm import Session
from typing import Optional, List
from DB.Engine.CRUD import BaseCRUD  # Базовый CRUD-класс
from DB.Models.Page import Page  # Модель Page


class EnginePage(BaseCRUD):
    """
    Класс EnginePage предоставляет удобный интерфейс для работы с таблицей Page в базе данных.
    Инкапсулирует CRUD-логику и дополнительные методы, специфичные для страниц.
    """

    def __init__(self, session: Session=None):        
        """        Инициализация EnginePage.

        :param session: Объект сессии SQLAlchemy для выполнения операций с БД.
        """
                
        super().__init__(session=session, model=Page)

    def add_page(self, *, index:int , name: str, description: Optional[str] = None) -> bool:
        """
        Добавляет новую страницу.

        :param name: Имя HTML-файла страницы (например, "screen_2_mass_load.html").
        :param description: Описание страницы.
        :return: True, если запись успешно добавлена, иначе False.
        """
        return self.add(index=index, name=name, description=description)

    def find_page(self, name: str) -> bool:
        """
        Проверяет, есть ли в таблице запись с полем name == name.

        :param name: Имя страницы (например, "screen_2_mass_load.html").
        :return: True, если есть, иначе False.
        """
        return (
                self.session
                .query(self.model)
                .filter_by(name=name)
                .first() is not None
        )

    def get_page_by_id(self, page_id: int) -> Optional[Page]:
        """
        Получает страницу по её уникальному идентификатору.

        :param page_id: ID страницы.
        :return: Объект Page или None, если не найден.
        """
        return self.get(page_id)

    def update_page(
            self,
            page_id: int,
            name: Optional[str] = None,
            description: Optional[str] = None
    ) -> bool:
        """
        Обновляет поля страницы.

        :param page_id: ID страницы.
        :param name: Новое имя файла страницы.
        :param description: Новое описание.
        :return: True, если обновление прошло успешно, иначе False.
        """
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        return self.update(index=page_id, **updates)

    def delete_page(self, page_id: int) -> bool:
        """
        Удаляет страницу по её ID.

        :param page_id: ID страницы.
        :return: True, если удаление прошло успешно, иначе False.
        """
        return self.delete(index=page_id)

    def get_all_pages(self) -> List[Page]:
        """
        Возвращает список всех страниц.

        :return: Список объектов Page.
        """
        return self.all()
