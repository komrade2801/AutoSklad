import traceback
from sqlalchemy.orm import Session
from typing import Optional, List

from Core.app_logging import get_logger
from DB.Engine.CRUD import BaseCRUD  # Импортируем BaseCRUD

logger = get_logger(__name__)
from ..Models.Group import Group  # Импортируем модель Error


class EngineGroup(BaseCRUD):
    """
    Класс EngineGroup предоставляет удобный интерфейс для работы с таблицей Group в базе данных
    Он инкапсулирует логику CRUD операций и предоставляет дополнительные методы, специфичные для Group
    """

    def __init__(self, session: Session=None):        
        """        Инициализация класса EngineGroup

        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных
        """
                
        super().__init__(session=session, model=Group)

    def add_group(self,
                  index: Optional[int],
                  name: Optional[str] = None,
                  description: Optional[str] = None,
                  paren_group_id: Optional[int] = None
                  ) -> bool:
        """
         Добавляет новую группу в таблицу Group.
        :param index: Уникальный идентификатор.
        :param name: Название группы.
        :param description: Описание группы.
        :param paren_group_id: Статус группы (например, активна/не активна).
        :return: True если группа успешно добавлена, иначе False.
        """
        logger.debug("[EngineGroup.add_group] index=%s, name=%s, description=%s, paren_group_id=%s",
                     index, name, description, paren_group_id)
        try:
            result = self.add(
                index=index,
                name=name,
                description=description,
                paren_group_id=paren_group_id
            )
            logger.debug("[EngineGroup.add_group] Результат add: %s", result)
            return result
        except Exception as e:
            logger.exception("[EngineGroup.add_group] ОШИБКА при добавлении группы: %s", e)
            return False

    def get_group_by_id(self, group_id: int) -> Optional[Group]:
        """
        Получает группу из таблицы Group по уникальному идентификатору.

        :param group_id: Уникальный идентификатор группы.
        :return: Объект Group или None, если группа не найдена.
        """
        return self.get(group_id)

    def find_groups_by_name(self, name: str) -> List[Group]:
        """
        Получает группу из таблицы Group по уникальному идентификатору.

        :param name: Название группы.
        :return: Объект Group или None, если группа не найдена.
        """
        tool_types = self.session.query(Group).filter(Group.name == name).all()
        tool_types.sort(key=lambda rec: rec.id, reverse=False)
        return tool_types

    def update_group(self,
            group_id: int,
            name: Optional[str] = None,
            description: Optional[str] = None,
            paren_group_id: Optional[int] = None
        ) -> bool:
        """
        Обновляет данные группы по уникальному идентификатору.

        :param group_id: Уникальный идентификатор группы.
        :param name: Новое название группы.
        :param description: Новое описание группы.
        :param paren_group_id: Новый статус группы.
        :return: True если группа успешно обновлена, иначе False.
        """
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if paren_group_id is not None:
            updates["paren_group_id"] = paren_group_id
        return self.update(index=group_id, **updates)

    def delete_group(self, group_id: int) -> bool:
        """
        Удаляет группу по уникальному идентификатору.

        :param group_id: Уникальный идентификатор группы.
        :return: True если группа успешно удалена, иначе False.
        """
        return self.delete(index=group_id)

    def get_all_groups(self) -> List[Group]:
        """
        Получает все группы из таблицы Group.

        :return: Список всех групп в таблице Group.
        """
        return self.all()

    def get_groups_by_paren_group_id(self, paren_group_id: int) -> List[Group]:
        """
        Получает все группы с определённым статусом.

        :param paren_group_id: Статус группы (например, активна/не активна).
        :return: Список объектов Group с заданным статусом.
        """
        return self.session.query(self.model).filter_by(paren_group_id=paren_group_id).all()

    def get_cells_by_group(self, group_id: int) -> Optional[List]:
        """
        Получает все связанные объекты Cell для заданной группы.

        :param group_id: Уникальный идентификатор группы.
        :return: Список объектов Cell или None, если группа не найдена.
        """
        group = self.get_group_by_id(group_id)
        if group:
            return group.cells
        return None

    def get_tools_by_group(self, group_id: int) -> Optional[List]:
        """
        Получает все связанные объекты Tools для заданной группы.

        :param group_id: Уникальный идентификатор группы.
        :return: Список объектов Tools или None, если группа не найдена.
        """
        group = self.get_group_by_id(group_id)
        if group:
            return group.tools
        return None

    def create_group(self,
                name: str,
                description: str,
                paren_group_id: int = 1
           ) -> Optional[Group]:
        """
        Создаёт новую группу с заданными именем и описанием.
        Генерирует новый уникальный идентификатор на основе максимального существующего значения.

        :param name: Название группы.
        :param description: Описание группы.
        :param paren_group_id: Статус группы (по умолчанию 1, т.е. активна).
        :return: Объект созданной группы или None, если создание не удалось.
        """
        logger.debug("[EngineGroup.create_group] name=%s, description=%s, paren_group_id=%s",
                     name, description, paren_group_id)
        
        # Получаем все существующие ID для проверки
        all_ids = self.get_all_ids()
        logger.debug("[EngineGroup.create_group] Существующие ID в БД: %s", all_ids)
        
        # Генерируем следующий свободный ID
        if all_ids:
            max_id = max(all_ids)
            # Ищем первый свободный ID начиная с max_id + 1
            new_id = max_id + 1
            # Проверяем, не занят ли ID (на случай, если есть пропуски)
            while new_id in all_ids:
                new_id += 1
        else:
            new_id = 1
        
        logger.debug("[EngineGroup.create_group] Сгенерирован новый ID: %s", new_id)
        
        # Дополнительная проверка, не существует ли уже группа с таким ID
        existing_with_id = self.get_group_by_id(new_id)
        if existing_with_id:
            logger.warning("[EngineGroup.create_group] Группа с ID %s уже существует", new_id)
            # Ищем следующий свободный ID
            all_ids_set = set(all_ids)
            candidate_id = new_id + 1
            while candidate_id in all_ids_set:
                candidate_id += 1
            new_id = candidate_id
            logger.debug("[EngineGroup.create_group] Используем следующий свободный ID: %s", new_id)
        
        try:
            add_result = self.add_group(index=new_id, name=name, description=description, paren_group_id=paren_group_id)
            logger.debug("[EngineGroup.create_group] Результат add_group: %s", add_result)
            
            if add_result:
                # Принудительно очищаем кеш и сбрасываем состояние сессии
                self._cache.clear()
                self.session.expire_all()  # Сбрасываем кеш сессии, чтобы перечитать из БД
                logger.debug("[EngineGroup.create_group] Кеш и сессия очищены, ID=%s", new_id)
                
                # Пробуем получить через прямую сессию для отладки
                try:
                    direct_query = self.session.query(self.model).filter_by(id=new_id).first()
                    logger.debug("[EngineGroup.create_group] Прямой запрос к БД для ID %s: %s", new_id, direct_query)
                except Exception as e:
                    logger.exception("[EngineGroup.create_group] Ошибка при прямом запросе: %s", e)
                
                created_group = self.get_group_by_id(new_id)
                logger.debug("[EngineGroup.create_group] Получена созданная группа: %s", created_group)
                
                if not created_group:
                    # Пробуем найти по имени
                    groups_by_name = self.find_groups_by_name(name)
                    logger.debug("[EngineGroup.create_group] По имени '%s' найдено групп: %s", name, len(groups_by_name))
                    if groups_by_name:
                        logger.debug("[EngineGroup.create_group] Найденные группы: %s", [g.id for g in groups_by_name])
                
                return created_group
        except Exception as e:
            logger.exception("[EngineGroup.create_group] ОШИБКА при создании группы: %s", e)
            return None
        
        logger.error("[EngineGroup.create_group] add_group вернул False, группа не создана")
        return None

    def find(self, name, description) -> Optional[Group]:
        """
        Ищет группу по заданному имени. Если группа с указанным именем (или содержащая его)
        не найдена, создаёт новую группу с заданными именем и описанием.

        Аргументы:
            name (str): Фрагмент или полное имя группы для поиска. Если имя группы содержит
                данный фрагмент, группа считается найденной.
            description (str): Описание для новой группы, которое используется только если
                группа не была найдена.

        Возвращает:
            Optional[Group]: Найденная или созданная группа. Если по каким-либо причинам группа
                не может быть найдена или создана, возвращается None.
        """
        groups = self.get_all_groups()
        target_group = None
        for group in groups:

            if group.name and name in group.name:
                target_group = group

        if not target_group:
            index = max(self.get_all_ids(), default=0) + 1
            self.add_group(
                index=index,
                name=name,
                description=description,
                paren_group_id=0,
            )

            target_group = self.get_group_by_id(index)

        return target_group
