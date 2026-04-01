from typing import List, Optional

# from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.ToolTypesCRUD import EngineToolTypes
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.UserCRUD import EngineUser
from DB.Models.History import History
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice


class EngineHistoryOperation:
    """
    Сервис для работы с операциями истории через CRUD-репозитории.

    Использует EngineHistory и EngineToolsHasDevice вместо прямых session-запросов.
    """

    def __init__(
            self,
            history_crud: EngineHistory = None,
            tools_has_device: EngineToolsHasDevice = None
    ):
        """
        Инициализация сервиса.

        :param history_crud: Репозиторий EngineHistory.
        :param tools_has_device: Репозиторий EngineToolsHasDevice.
        """
        self.history_crud = history_crud or EngineHistory()
        self.tools_has_device = tools_has_device or EngineToolsHasDevice()
        # self.tool_crud = EngineTools()
        self.tool_types_crud = EngineToolTypes()
        self.user_crud = EngineUser()
        self.plan_crud = EnginePlan()

    def _transform_history_record(self, record: History) -> dict:
        """
        Преобразует объект History в словарь для API-ответа.

        :param record: Экземпляр History.
        :return: Словарь с полями date, name_operation, tool, plan, user, device.
        """
        date_str = record.datetime.strftime("%H:%M:%S %d.%m.%Y") if record.datetime else "None"
        name_operation = record.description or "None"
        plan = self.plan_crud.get_plan_by_id(record.plan_id) if record.plan_id else None

        # Получаем имя пользователя (отчество опционально)
        if record.user_id:
            user = self.user_crud.get(record.user_id)
            if user:
                family = (user.family or "").strip()
                first_name = (user.first_name or "").strip()
                second_name = (user.second_name or "").strip()

                initials = []
                if first_name:
                    initials.append(f"{first_name[0]}.")
                if second_name:
                    initials.append(f"{second_name[0]}.")

                short_name = " ".join(initials).strip()
                if family and short_name:
                    user_name = f"{family} {short_name}"
                elif family:
                    user_name = family
                elif short_name:
                    user_name = short_name
                else:
                    user_name = "Unknown"
            else:
                user_name = "Unknown"
        else:
            user_name = "None"

        # Получаем название инструмента
        if record.tools_id:
            tool_type = self.tool_types_crud.get(record.tools_id)
            tool_name = tool_type.name if tool_type else "Unknown"
        else:
            tool_name = "None"

        plan_name = plan.designation if plan else "Без чертежа"

        return {
            "date": date_str,
            "status": record.status,
            "name_operation": name_operation,
            "tool": tool_name,
            "plan": plan_name,
            "user": user_name,
        }

    def get_operations_by_device_id(self, device_id: int) -> List[dict]:
        """
        Возвращает список операций истории для заданного устройства.

        :param device_id: ID устройства.
        :return: Список словарей-операций.
        """
        # tool_ids = self.tools_has_device.get_tools_by_device_id(device_id)
        # if not tool_ids:
        #     return []
        # фильтрация через CoreEngine.filter
        histories = self.history_crud.all()
        return [self._transform_history_record(h) for h in histories]

    def create_operation(self, op_data) -> Optional[dict]:
        """
        Создает операцию истории.

        :param op_data: Pydantic-модель или dict с полями History.
        :return: Словарь новой операции или None.
        """
        data = op_data.dict() if hasattr(op_data, 'dict') else dict(op_data)
        # id должен быть в поле 'id' или передан как index
        index = data.pop('id', 0)
        success = self.history_crud.add(index=index, **data)
        if not success:
            return None
        record = self.history_crud.get(index)
        return self._transform_history_record(record) if record else None

    def get_operation_by_id(self, op_id: int) -> Optional[dict]:
        """
        Возвращает операцию по ID.
        """
        record = self.history_crud.get(op_id)
        return self._transform_history_record(record) if record else None

    def update_operation(self, op_id: int, op_data) -> Optional[dict]:
        """
        Обновляет операцию истории.
        """
        data = op_data.dict() if hasattr(op_data, 'dict') else dict(op_data)
        updated = self.history_crud.update(index=op_id, **data)
        if not updated:
            return None
        record = self.history_crud.get(op_id)
        return self._transform_history_record(record) if record else None

    def delete_operation(self, op_id: int) -> bool:
        """
        Удаляет операцию истории.

        :param op_id: ID операции.
        :return: True при успешном удалении.
        """
        return self.history_crud.delete(index=op_id)
