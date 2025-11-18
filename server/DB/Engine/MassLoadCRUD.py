from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
# from sqlalchemy.exc import IntegrityError
from DB.Engine.CRUD import BaseCRUD
from ..Models.Load import Load
from ..Models.MassLoad import MassLoad  # Импорт модели MassDrop
from ..Models.Tools import Tools


class EngineMassLoad(BaseCRUD):
    """
    Класс EngineMassLoad наследует от BaseCRUD и предоставляет интерфейс для работы с моделью MassLoad.
    Использует все методы из BaseCRUD для выполнения операций с таблицей MassLoad.
    """

    def __init__(self, session: Session = None):
        """        Инициализация EngineMassLoad.

        :param session: Сессия SQLAlchemy для выполнения операций с базой данных.
        """
        # Инициализация родительского класса с переданными session и моделью MassLoad

        super().__init__(session=session, model=MassLoad)

    def add_mass_load(self, description: str, status_id: int, index: int) -> bool:
        """
        Добавляет новую задачу массовой загрузки.

        :param description: Описание задачи массовой загрузки.
        :param index: Индекс задачи.
        :return: True, если задача успешно добавлена, иначе False.
        """

        return self.add(index=index, description=description, status_id=status_id, created_at=datetime.now())
        # try:except IntegrityError as e:
        #      print(f"Ошибка добавления задачи массовой загрузки: {e}")
        #     return False

    def update_mass_load(self, mass_load_id: int, description: Optional[str] = None) -> bool:
        """
        Обновляет задачу массовой загрузки.

        :param mass_load_id: Уникальный идентификатор задачи.
        :param description: Новое описание задачи (опционально).
        :return: True, если обновление выполнено успешно, иначе False.
        """
        fields_to_update = {}
        if description is not None:
            fields_to_update["description"] = description
        return self.update(mass_load_id, **fields_to_update)

    def delete_mass_load(self, mass_load_id: int) -> bool:
        """
        Удаляет задачу массовой загрузки по её идентификатору.

        :param mass_load_id: Уникальный идентификатор задачи.
        :return: True, если задача успешно удалена, иначе False.
        """
        return self.delete(index=mass_load_id)

    def delete_all_mass_loads(self) -> bool:
        """
        Удаляет все задачи массовой загрузки из таблицы.

        :return: True, если таблица успешно очищена, иначе False.
        """

        return self.drop()  # Используем метод drop из BaseCRUD для удаления таблицы
        # try:except Exception as e:
        #  print(f"Ошибка при удалении всех задач массовой загрузки: {e}")
        # return False

    def get_mass_load_by_id(self, mass_load_id: int) -> Optional[MassLoad]:
        """
        Возвращает задачу массовой загрузки по её идентификатору.

        :param mass_load_id: Уникальный идентификатор задачи.
        :return: Объект MassLoad или None, если задача не найдена.
        """
        return self.get(mass_load_id)

    def get_by_plan(self, plan_id: int) -> List[MassLoad]:
        """
        Возвращает все записи MassLoad, связанные с данным планом.

        :param plan_id: Идентификатор плана.
        :return: Список объектов MassLoad.
        """
        return (
            self.session.query(MassLoad)
            .join(Load, Load.mass_load_id == MassLoad.id)
            .join(Tools, Load.tools_id == Tools.id)
            .filter(Tools.plan_id == plan_id)
            .options(joinedload(MassLoad.loads))
            .all()
        )

    def delete_by_plan(self, plan_id: int) -> bool:
        """
        Удаляет все записи MassLoad, связанные с данным plan_id.

        :param plan_id: Идентификатор плана.
        :return: True, если хотя бы одна запись была удалена, иначе False.
        """
        mass_loads = self.get_by_plan(plan_id)
        if not mass_loads:
            return False

        for mass_load in mass_loads:
            self.session.delete(mass_load)

        self.session.commit()
        return True

    def update_by_plan(self, plan_id: int, **kwargs) -> bool:
        """
        Обновляет все записи MassLoad, связанные с данным plan_id.

        :param plan_id: Идентификатор плана.
        :param kwargs: Поля для обновления.
        :return: True, если обновление прошло успешно, иначе False.
        """
        mass_loads = self.get_by_plan(plan_id)
        if not mass_loads:
            return False

        for mass_load in mass_loads:
            for key, value in kwargs.items():
                setattr(mass_load, key, value)

        self.session.commit()
        return True

    def get_free(self) -> List[MassLoad]:
        """
        Возвращает список "свободных" задач массовой загрузки, т.е. тех записей MassLoad,
        для которых связанный инструмент (через таблицу Load) не привязан к чертежу (Tools.plan_id is None).
        """
        query = (
            self.session.query(MassLoad)
            .join(Load, Load.mass_load_id == MassLoad.id)
            .join(Tools, Load.tools_id == Tools.id)
            .filter(Tools.plan_id == None)
            .options(joinedload(MassLoad.loads))
        )
        return query.all()

    def delete_free(self) -> bool:
        """
        Удаляет все "свободные" задачи массовой загрузки (те, для которых Tools.plan_id IS NULL).
        """
        free_tasks = self.get_free()
        if not free_tasks:
            return False

        for task in free_tasks:
            self.session.delete(task)
        self.session.commit()
        return True

    def update_free(self, description, devices, loads) -> bool:
        """
        Обновляет все "свободные" задачи массовой загрузки.
        - Если задано новое описание, обновляет его.
        - Если переданы новые записи loads, удаляет старые связанные записи из таблицы Load и добавляет новые.

        :param devices:
        :param description: Новое описание, если требуется обновление.
        :param loads: Новый список объектов Load для обновления связи.
        :return: True, если обновление прошло успешно, иначе False.
        """
        free_tasks = self.get_free()
        if not free_tasks:
            return False

        for task in free_tasks:
            if description is not None:
                task.description = description
            if loads is not None:
                # Удаляем старые Load, связанные с задачей
                old_loads = self.session.query(Load).filter_by(mass_load_id=task.id).all()
                for old in old_loads:
                    self.session.delete(old)
                # Добавляем новые Load и связываем с задачей
                for load in loads:
                    load.mass_load_id = task.id
                    self.session.add(load)
        self.session.commit()
        return True

    def add_free(self, description, devices, loads) -> Optional[MassLoad]:
        """
        Создает новую "свободную" задачу массовой загрузки (MassLoad), не привязанную к чертежу.
        - Создает новую запись MassLoad с заданным описанием.
        - Если переданы записи Load, устанавливает для них mass_load_id новой задачи.

        :param devices:
        :param description: Описание задачи.
        :param loads: Список объектов Load для привязки к задаче.
        :return: Созданный объект MassLoad или None, если создание не удалось.
        """
        last_task = self.session.query(MassLoad).order_by(MassLoad.id.desc()).first()
        new_id = last_task.id + 1 if last_task else 1
        if self.add(index=new_id, description=description, created_at=datetime.now()):
            new_task = self.get(new_id)
            if loads:
                for load in loads:
                    load.mass_load_id = new_task.id
                    self.session.add(load)
            self.session.commit()
            return new_task
        return None
