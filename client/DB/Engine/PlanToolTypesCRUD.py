from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

# from DB.Data.db import SessionLocal
from ..Engine.BaseCRUD import BaseCRUD
from ..Models.PlanToolTypes import PlanToolTypes


class EnginePlanToolTypes(BaseCRUD):
    """
    Класс EnginePlanToolTypes предоставляет удобный интерфейс для работы с таблицей PlanToolTypes.
    Поддерживает CRUD-операции и дополнительные методы, специфичные для чертежей.
    """

    def __init__(self, session: Session = None):
        """        Инициализация класса EnginePlan

        :param session: Объект сессии SQLAlchemy.
        """

        super().__init__(session=session, model=PlanToolTypes)

    def add_plan_tool_types(
            self,
            index: Optional[int],
            tool_types_id: Optional[str],
            tool_types_count: Optional[str],
            plan_id: Optional[str],
    ) -> bool:
        """
         Добавляет новую связь в таблицу PlanToolTypes.
        :param index: Уникальный идентификатор.
        :param tool_types_id: Идентификатор инструмента.
        :param tool_types_count: Количество инструмента.
        :param plan_id: Идентификатор чертежа.
        """
        return self.add(
            index=index,
            tool_types_id=tool_types_id,
            tool_types_count=tool_types_count,
            plan_id=plan_id,
        )

    def get_plan_tool_types_by_id(self, plan_tool_types_id: int) -> Optional[PlanToolTypes]:
        """
        Получает чертеж по его уникальному идентификатору.

        :param plan_tool_types_id: Уникальный идентификатор чертежа.
        :return: Объект PlanToolTypes или None, если чертеж не найден.
        """
        return self.get(plan_tool_types_id)

    def get_plan_tool_types_by_ids(self, plan_tool_types_ids) -> List[PlanToolTypes]:
        """
        Возвращает список чертежей по списку идентификаторов.

        :param plan_tool_types_ids: Список уникальных идентификаторов связей.
        :return: Список объектов PlanToolTypes.
        """
        return self.session.query(self.model).filter(self.model.id.in_(plan_tool_types_ids)).all()

    def get_plan_tool_types_by_tool_types_id(self, tool_types_id: int) -> List[PlanToolTypes]:
        """
        Возвращает список чертежей по названию предприятия.

        :param tool_types_id: Идентификатор инструмента.
        :return: Список объектов PlanToolTypes.
        """
        return self.session.query(self.model).filter_by(tool_types_id=tool_types_id).all()

    def get_plan_tool_types_by_plan_id(self, plan_id: int) -> List[PlanToolTypes]:
        """
        Возвращает список чертежей по названию предприятия.

        :param plan_id: Идентификатор чертежа.
        :return: Список объектов PlanToolTypes.
        """
        return self.session.query(self.model).filter_by(plan_id=plan_id).all()

    def update_plan_tool_types_tool_types(self, plan_tool_types_id: int, **kwargs) -> bool:
        """
        Обновляет информацию о чертеже по его уникальному идентификатору.

        :param plan_tool_types_id: Уникальный идентификатор связи.
        :param kwargs: Поля и значения для обновления записи.
        :return: True, если запись успешно обновлена, иначе False.
        """
        return self.update(plan_tool_types_id, **kwargs)

    def delete_plan_tool_types(self, plan_tool_types_id: int) -> bool:
        """
        Удаляет чертеж по уникальному идентификатору.

        :param plan_tool_types_id: Уникальный идентификатор связи.
        :return: True, если чертеж успешно удален, иначе False.
        """
        return self.delete(index=plan_tool_types_id)

    def get_all_plan_tool_types(self) -> List[PlanToolTypes]:
        """
        Возвращает список всех чертежей в таблице Plan.

        :return: Список всех чертежей.
        """
        return self.all()

    def get_plan_tool_types_with_relations(self, plan_tool_types_id: int) -> Optional[PlanToolTypes]:
        """
        Получает чертеж вместе со связанными объектами (инструменты, истории, дочерние чертежи).

        :param plan_tool_types_id: Уникальный идентификатор связи.
        :return: Объект Plan или None.
        """
        return (
            self.session.query(self.model)
            .filter_by(id=plan_tool_types_id)
            .options(
                joinedload(self.model.tools),
                joinedload(self.model.plans)
            )
            .one_or_none()
        )

    def create_plan_tool_types(self,
                    index: int = None,
                    tool_types_id: int = None,
                    tool_types_count: int = None,
                    plan_id: int = None,
                    ) -> Optional[PlanToolTypes]:
        """
        Создает новый чертеж с заданным именем.
        Для остальных полей используются значения по умолчанию:
        :param tool_types_id: - tool_types_id: None.
        :param tool_types_count: - tool_types_count: None,
        :param plan_id: - plan_id: 0
        :return: Объект созданного чертежа или None, если создание не удалось.
        """
        last_plan = self.session.query(self.model).order_by(self.model.id.desc()).first()
        new_id = last_plan.id + 1 if last_plan else 1

        if self.add_plan(
                index=index,
                tool_types_id=tool_types_id,
                tool_types_count=tool_types_count,
                plan_id=plan_id,
        ):
            return self.get_plan_by_id(new_id)
        return None

    def update_plan_tool_types_from_data(self, plan_tool_types_id, plan_tool_types_data):
        plan_tool_types = self.get(plan_tool_types_id)
        if hasattr(plan_tool_types_data, "id"):
            plan_tool_types_id = plan_tool_types_data.id
        else:
            plan_tool_types_id = plan_tool_types.id
        if hasattr(plan_tool_types_data, "tool_types_id"):
            tool_types_id = plan_tool_types_data.tool_types_id
        else:
            tool_types_id = plan_tool_types.tool_types_id
        if hasattr(plan_tool_types_data, "tool_types_count"):
            tool_types_count = plan_tool_types_data.tool_types_count
        else:
            tool_types_count = plan_tool_types.tool_types_count
        if hasattr(plan_tool_types_data, "plan_id"):
            plan_id = plan_tool_types_data.plan_id
        else:
            plan_id = plan_tool_types.plan_id
        self.update(
            index=plan_tool_types_id,
            tool_types_id=tool_types_id,
            tool_types_count=tool_types_count,
            plan_id=plan_id
        )
        return self.get(plan_tool_types_id)

    def update_plan_tool_types_by_name(self, plan_tool_types_id, param):
        pass
