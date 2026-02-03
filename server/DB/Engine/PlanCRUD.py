from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

# from DB.Data.db import SessionLocal
from DB.Engine.CRUD import BaseCRUD
from DB.Models.Plan import Plan


class EnginePlan(BaseCRUD):
    """
    Класс EnginePlan предоставляет удобный интерфейс для работы с таблицей Plan.
    Поддерживает CRUD-операции и дополнительные методы, специфичные для чертежей.
    """

    def __init__(self, session: Session=None):        
        """        Инициализация класса EnginePlan

        :param session: Объект сессии SQLAlchemy.
        """
                
        super().__init__(session=session, model=Plan)

    def add_plan(
            self,
            index: Optional[int],
            enterprise: Optional[str],
            barcode: Optional[str],
            name: Optional[str],
            description: Optional[str],
            designation: Optional[str],
            index_list: Optional[int],
            list_count: Optional[int],
            hidden: Optional[bool],
            parent_plan: Optional[int],
            parent_plan_id: Optional[int]= None,
    ) -> bool:
        """
         Добавляет новый чертеж в таблицу Plan.
        :param index: Уникальный идентификатор.
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
            index=index,
            enterprise=enterprise,
            barcode=barcode,
            name=name,
            description=description,
            designation=designation,
            index_list=index_list,
            list_count=list_count,
            hidden=hidden,
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

    def get_last_plan_by_designation(self, designation: str) -> Optional[Plan]:
        """
        Получает чертеж по штрих-коду.

        :param designation: Обозначение чертежа.
        :return: Объект Plan или None, если чертеж не найден.
        """
        return self.session.query(self.model).filter_by(designation=designation).order_by(Plan.id.desc()).first()

    def get_plans_by_designation(self, designation: str) -> List[Plan]:
        """
        Получает чертеж по штрих-коду.

        :param designation: Обозначение чертежа.
        :return: Объект Plan или None, если чертеж не найден.
        """
        return self.session.query(self.model).filter_by(designation=designation).all()

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
        return self.session.query(self.model).filter_by(parent_plan_id=parent_plan_id).all()

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
        return self.delete(index=plan_id)

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

    def get_plans_by_ids(self, plan_ids) -> List[Plan]:
        """
        Возвращает список чертежей по списку идентификаторов.

        :param plan_ids: Список уникальных идентификаторов чертежей.
        :return: Список объектов Plan.
        """
        return self.session.query(self.model).filter(self.model.id.in_(plan_ids)).all()


    def create_plan(self,
                    index:int =None,
                    enterprise:str =None,
                    barcode:str =None,
                    name:str =None,
                    description:str =None,
                    designation:str =None,
                    index_list:int =None,
                    list_count:int =None,
                    parent_plan:int =None,
                    parent_plan_id:int =None,
                    ) -> Optional[Plan]:
        """
        Создает новый чертеж с заданным именем.
        Для остальных полей используются значения по умолчанию:
        :param parent_plan_id: - parent_plan_id: None.
        :param parent_plan: - parent_plan: None,
        :param list_count: - list_count: 0,
        :param index_list: - index_list: 0,
        :param designation: - designation: пустая строка,
        :param description: - description: пустая строка,
        :param barcode: - barcode: пустая строка,
        :param enterprise: - enterprise: пустая строка,
        :param index: - Новый идентификатор генерируется на основе максимального существующего.
        :param name: - Название нового чертежа.
        :return: Объект созданного чертежа или None, если создание не удалось.
        """
        last_plan = self.session.query(self.model).order_by(self.model.id.desc()).first()
        new_id = last_plan.id + 1 if last_plan else 1

        if self.add_plan(
            index=index,
            enterprise=enterprise,
            barcode=barcode,
            name=name,
            description=description,
            designation=designation,
            index_list=index_list,
            list_count=list_count,
            parent_plan=parent_plan,
            parent_plan_id=parent_plan_id
        ):
            return self.get_plan_by_id(new_id)
        return None

    def update_plan_from_data(self, plan_id, plan_data):
        plan = self.get(plan_id)
        if hasattr(plan_data, "id"):
            plan_id = plan_data.id
        else:
            plan_id = plan.id
        if hasattr(plan_data, "enterprise"):
            plan_enterprise = plan_data.enterprise
        else:
            plan_enterprise = plan.enterprise
        if hasattr(plan_data, "barcode"):
            plan_barcode = plan_data.barcode
        else:
            plan_barcode = plan.barcode
        if hasattr(plan_data, "name"):
            plan_name = plan_data.name
        else:
            plan_name = plan.plan_name
        if hasattr(plan_data, "description"):
            plan_description = plan_data.description
        else:
            plan_description = plan.description
        if hasattr(plan_data, "designation"):
            plan_designation = plan_data.designation
        else:
            plan_designation = plan.designation
        if hasattr(plan_data, "index_list"):
            plan_index_list = plan_data.index_list
        else:
            plan_index_list = plan.index_list
        if hasattr(plan_data, "list_count"):
            plan_list_count = plan_data.list_count
        else:
            plan_list_count = plan.list_count
        if hasattr(plan_data, "parent_plan"):
            plan_parent_plan = plan_data.parent_plan
        else:
            plan_parent_plan = plan.parent_plan
        if hasattr(plan_data, "parent_plan_id"):
            plan_parent_plan_id = plan_data.parent_plan_id
        else:
            plan_parent_plan_id = plan.parent_plan_id
        self.update(
            index=plan_id,
            enterprise=plan_enterprise,
            barcode=plan_barcode,
            name=plan_name,
            description=plan_description,
            designation=plan_designation,
            index_list=plan_index_list,
            list_count=plan_list_count,
            parent_plan=plan_parent_plan,
            parent_plan_id=plan_parent_plan_id
        )
        return self.get(plan_id)


    def update_plan_by_name(self, plan_id, param):
        pass
