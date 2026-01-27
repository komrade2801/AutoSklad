from datetime import datetime

from sqlalchemy.orm import Session, joinedload
# from sqlalchemy.exc import IntegrityError
from typing import Optional, List

from DB.Models.Drop import Drop
# from DB.Models.Plan import Plan
from DB.Models.Tools import Tools
from DB.Models.MassDropHasDevice import MassDropHasDevice
from .CRUD import BaseCRUD
from ..Models.MassDrop import MassDrop  # Импорт модели MassDrop
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker


class EngineMassDrop(BaseCRUD):
    """
    Класс EngineMassDrop, наследующий возможности BaseCRUD для работы с таблицей MassDrop.
    """

    def __init__(self, session: Session=None):
        """
        Инициализация EngineMassDrop.

        :param session: Объект сессии SQLAlchemy для работы с базой данных.
        """
        super().__init__(session=session, model=MassDrop)

    def add_task(self,
             index: int,
             created_at: datetime,
             description: Optional[str] = None
        ) -> bool:
        """
        Добавляет новую задачу массового удаления.

        :param index:
        :param description: Описание задачи.
        :return: True если задача успешно добавлена, иначе False.
        """
        return self.add(index=index, created_at=created_at, description=description)

    def get_task(self, task_id: int) -> Optional["MassDrop"]:
        """
        Возвращает задачу по её уникальному идентификатору.

        :param task_id: Идентификатор задачи.
        :return: Объект задачи или None, если задача не найдена.
        """
        return self.get(task_id)

    def get_all_tasks(self) -> List["MassDrop"]:
        """
        Возвращает список всех задач массового удаления.

        :return: Список объектов MassDrop.
        """
        return self.all()

    def update_task(self, task_id: int, description: Optional[str] = None) -> bool:
        """
        Обновляет описание задачи.

        :param task_id: Идентификатор задачи.
        :param description: Новое описание задачи.
        :return: True если обновление прошло успешно, иначе False.
        """
        return self.update(task_id, description=description)

    def delete_task(self, task_id: int) -> bool:
        """
        Удаляет задачу по её уникальному идентификатору.

        :param task_id: Идентификатор задачи.
        :return: True если удаление прошло успешно, иначе False.
        """
        return self.delete(index=task_id)

    def count_tasks(self) -> int:
        """
        Возвращает количество задач в таблице.

        :return: Число задач.
        """
        return self.count()

    def drop_table(self) -> bool:
        """
        Удаляет таблицу MassDrop из базы данных.

        :return: True если таблица успешно удалена, иначе False.
        """
        return self.drop()


    def get_by_plan(self, plan_id: int) -> List[MassDrop]:
        """Возвращает все записи MassDrop, связанные с plan_id."""
        return (
            self.session.query(MassDrop)
            .join(Drop, Drop.mass_drop_id == MassDrop.id)
            .join(Tools, Drop.tools_id == Tools.id)
            .filter(Tools.plan_id == plan_id)
            .options(joinedload(MassDrop.drops))  # Загрузка связанных Drop
            .all()
        )


    def delete_by_plan(self, plan_id: int) -> bool:
        """Удаляет все MassDrop и связанные данные по plan_id."""
        mass_drops = self.get_by_plan(plan_id)
        if not mass_drops:
            return False

        # Удаляем связи с устройствами (MassDropHasDevice)
        for mass_drop in mass_drops:
            self.session.query(MassDropHasDevice).filter_by(mass_drop_id=mass_drop.id).delete()

        # Удаляем основные записи MassDrop
        self.session.query(MassDrop).filter(MassDrop.id.in_([md.id for md in mass_drops])).delete()
        self.session.commit()
        return True


    def update_by_plan(
            self,
            plan_id,
            description,
            devices,
            drops,
            plan
    ) -> bool:
        """Обновляет MassDrop и связанные данные по plan_id."""
        mass_drops = self.get_by_plan(plan_id)
        if not mass_drops:
            return False

        for mass_drop in mass_drops:
            # Обновление основных полей
            if description:
                mass_drop.description = description

            # Обновление связей с устройствами
            if devices:
                # Удаляем старые связи
                self.session.query(MassDropHasDevice).filter_by(mass_drop_id=mass_drop.id).delete()
                # Добавляем новые
                for device_id in devices:
                    self.session.add(MassDropHasDevice(mass_drop_id=mass_drop.id, device_id=device_id))

            # Обновление drops (если переданы)
            if drops:
                # Логика обновления связанных drops
                pass

        self.session.commit()
        return True


    def get_free(self) -> List[MassDrop]:
        """
        Возвращает список "свободных" задач, т.е. тех записей MassDrop,
        для которых через связь с Drop и Tools обнаруживается, что Tools.plan_id IS NULL.
        """
        from DB.Models.Tools import Tools  # Импортируем здесь для избежания циклических зависимостей
        query = (
            self.session.query(MassDrop)
            .join(Drop, Drop.mass_drop_id == MassDrop.id)
            .join(Tools, Drop.tools_id == Tools.id)
            .filter(Tools.plan_id == None)
            .options(joinedload(MassDrop.drops))
        )
        return query.all()

    def delete_free(self) -> bool:
        """
        Удаляет все "свободные" задачи, т.е. те записи MassDrop, для которых Tools.plan_id IS NULL.
        Также удаляет связи с устройствами из таблицы MassDropHasDevice.
        """
        free_tasks = self.get_free()
        if not free_tasks:
            return False

        for task in free_tasks:
            self.session.query(MassDropHasDevice).filter_by(mass_drop_id=task.id).delete()
        self.session.query(MassDrop).filter(MassDrop.id.in_([task.id for task in free_tasks])).delete(synchronize_session=False)
        self.session.commit()
        return True

    def update_free(self, description, devices, drops) -> bool:
        """
        Обновляет все "свободные" задачи.
        - Если задано новое описание, обновляет его.
        - Если передан список устройств, обновляет связи с устройствами (удаляет старые и добавляет новые).
        - Если переданы новые записи drops, удаляет старые связанные Drop и добавляет новые.
        """
        free_tasks = self.get_free()
        if not free_tasks:
            return False

        for task in free_tasks:
            if description:
                task.description = description
            if devices:
                # Удаляем старые связи
                self.session.query(MassDropHasDevice).filter_by(mass_drop_id=task.id).delete()
                # Добавляем новые связи
                for device_id in devices:
                    self.session.add(MassDropHasDevice(mass_drop_id=task.id, device_id=device_id))
            if drops:
                # Удаляем старые Drop, связанные с задачей
                self.session.query(Drop).filter_by(mass_drop_id=task.id).delete()
                # Добавляем новые Drop
                for drop in drops:
                    drop.mass_drop_id = task.id
                    self.session.add(drop)
        self.session.commit()
        return True

    def add_free(self, description, devices, drops) -> Optional[MassDrop]:
        """
        Создает новую "свободную" задачу (MassDrop), не привязанную к чертежу.
        - Создает новую запись MassDrop с заданным описанием.
        - Если передан список устройств, создает связи с ними.
        - Если переданы записи Drop, устанавливает для них mass_drop_id новой задачи.
        Возвращает созданную задачу или None, если создание не удалось.
        """
        last_task = self.session.query(MassDrop).order_by(MassDrop.id.desc()).first()
        new_id = last_task.id + 1 if last_task else 1
        if self.add(index=new_id, description=description):
            new_task = self.get(new_id)
            if devices:
                for device_id in devices:
                    self.session.add(MassDropHasDevice(mass_drop_id=new_task.id, device_id=device_id))
            if drops:
                for drop in drops:
                    drop.mass_drop_id = new_task.id
                    self.session.add(drop)
            self.session.commit()
            return new_task
        return None
