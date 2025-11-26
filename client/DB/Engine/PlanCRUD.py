from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

# from DB.Data.db import SessionLocal
from ..Engine.BaseCRUD import BaseCRUD
from ..Models.Plan import Plan


class EnginePlan(BaseCRUD):
    """
    Класс EnginePlan предоставляет удобный интерфейс для работы с таблицей Plan.
    Поддерживает CRUD-операции и дополнительные методы, специфичные для чертежей.
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EnginePlan

        :param session: Объект сессии SQLAlchemy.
        """
        super().__init__(session, Plan)

    def add_plan(
            self,
            plan_id: Optional[int],
            enterprise: Optional[str],
            barcode: Optional[str],
            name: Optional[str],
            description: Optional[str],
            designation: Optional[str],
            index_list: Optional[int],
            list_count: Optional[int],
            parent_plan: Optional[int],
            parent_plan_id: Optional[int]= None,
    ) -> bool:
        """
         Добавляет новый чертеж в таблицу Plan.
        :param plan_id: Уникальный идентификатор.
        :param parent_plan: Идентификатор сборочный чертёж.
        :param enterprise: Название предприятия.
        :param barcode: Штрих-код чертежа.
        :param name: Название чертежа.
        :param description: Описание чертежа.
        :param designation: Назначение чертежа.
        :param index_list: Идентификатор списка.
        :param list_count: Количество в списке.
        :param parent_plan_id: Идентификатор родительского чертежа.
        :return: True, если запись успешно добавлена, иначе False.
        """
        return self.add(
            id=plan_id,
            enterprise=enterprise,
            barcode=barcode,
            name=name,
            description=description,
            designation=designation,
            index_list=index_list,
            list_count=list_count,
            parent_plan_id=parent_plan_id,
            parent_plan=parent_plan,
        )

    def get_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        """
        Получает чертеж по его уникальному идентификатору.

        :param plan_id: Уникальный идентификатор чертежа.
        :return: Объект Plan или None, если чертеж не найден.
        """
        return self.get(plan_id)

    def get_plan_by_barcode(self, barcode: str) -> Optional[Plan]:
        """
        Получает чертеж по штрих-коду.

        :param barcode: Штрих-код чертежа.
        :return: Объект Plan или None, если чертеж не найден.
        """
        return self.session.query(self.model).filter_by(barcode=barcode).one_or_none()

    def get_plan_by_designation(self, designation: str) -> Optional[Plan]:
        """
        Получает чертеж по штрих-коду.

        :param designation: Обозначение чертежа.
        :return: Объект Plan или None, если чертеж не найден.
        """
        return self.session.query(self.model).filter_by(designation=designation).first()

    def get_plans_by_enterprise(self, enterprise: str) -> List[Plan]:
        """
        Возвращает список чертежей по названию предприятия.

        :param enterprise: Название предприятия.
        :return: Список объектов Plan.
        """
        return self.session.query(self.model).filter_by(enterprise=enterprise).all()

    def get_plans_by_parent(self, parent_plan_id: int) -> List[Plan]:
        """
        Получает все дочерние чертежи для указанного родительского чертежа.

        :param parent_plan_id: Идентификатор родительского чертежа.
        :return: Список дочерних чертежей.
        """
        return self.session.query(self.model).filter_by(ParentPlan_id=parent_plan_id).all()

    def get_hierarchy(self, plan_id: int) -> List[Plan]:
        """
        Получает иерархию чертежей, начиная с указанного чертежа.

        :param plan_id: Идентификатор корневого чертежа.
        :return: Список чертежей в иерархии (включая потомков).
        """
        plan = self.get_plan_by_id(plan_id)
        if not plan:
            return []
        return [plan] + plan.child_plans

    def update_plan(self, plan_id: int, **kwargs) -> bool:
        """
        Обновляет информацию о чертеже по его уникальному идентификатору.

        :param plan_id: Уникальный идентификатор чертежа.
        :param kwargs: Поля и значения для обновления записи.
        :return: True, если запись успешно обновлена, иначе False.
        """
        return self.update(plan_id, **kwargs)

    def delete_plan(self, plan_id: int) -> bool:
        """
        Удаляет чертеж по уникальному идентификатору.

        :param plan_id: Уникальный идентификатор чертежа.
        :return: True, если чертеж успешно удален, иначе False.
        """
        return self.delete(plan_id)

    def get_all_plans(self) -> List[Plan]:
        """
        Возвращает список всех чертежей в таблице Plan.

        :return: Список всех чертежей.
        """
        return self.all()

    def get_plan_with_relations(self, plan_id: int) -> Optional[Plan]:
        """
        Получает чертеж вместе со связанными объектами (инструменты, истории, дочерние чертежи).

        :param plan_id: Уникальный идентификатор чертежа.
        :return: Объект Plan или None.
        """
        return (
            self.session.query(self.model)
            .filter_by(id=plan_id)
            .options(
                joinedload(self.model.tools),
                joinedload(self.model.stories),
                joinedload(self.model.child_plans)
            )
            .one_or_none()
        )

