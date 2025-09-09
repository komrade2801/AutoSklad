from __future__ import annotations

from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.ToolsHasDevice import ToolsHasDevice


class EngineToolsHasDevice(BaseCRUD):
    """
    CRUD-интерфейс для связующей таблицы Tools_has_Device.
    Все операции выполняются через методы BaseCRUD с кешированием.
    """

    def __init__(self, session: Session = None):
        super().__init__(session=session, model=ToolsHasDevice)

    def add_link(self, tools_id: int, device_id: int) -> bool:
        """
        Добавляет связь между инструментом и устройством.
        :return: True, если добавлено успешно.
        """
        # 1) попытаться найти существующую пару
        existing = (
            self.session
            .query(self.model)
            .filter_by(tools_id=tools_id, device_id=device_id)
            .one_or_none()
        )
        if existing:
            return True

        # 2) если нет — вставляем новую
        instance = self.model(tools_id=tools_id, device_id=device_id)
        try:
            with self.transaction() as db:
                db.add(instance)
            # если коммит прошёл без Exception — сбросим кэш
            self._cache.clear()
            return True

        except RuntimeError as e:
            # RuntimeError от transaction(): вложенный IntegrityError
            if "UNIQUE constraint failed" in str(e):
                # кто‑то вставил за нас — просто сбросим транзакцию и вернём OK
                return True
            # для других ошибок — пробрасываем
            raise

    def get_link(self, tools_id: int, device_id: int) -> ToolsHasDevice | None:
        """
        Получает Одну запись связи по составному ключу.
        :return: Объект ToolsHasDevice или None.
        """
        # Динамический метод get_by_<field> возвращает список, поэтому берем первый элемент
        matches = self.get_by_tools_id(tools_id)
        for link in matches:
            if link.device_id == device_id:
                return link
        return None

    def get_all_links(self) -> list[ToolsHasDevice]:
        """
        Все связи инструментов и устройств.
        """
        return self.all()

    def delete_link(self, tools_id: int, device_id: int) -> bool:
        """
        Удаляет конкретную связь.
        :return: True, если связь была удалена.
        """
        link = self.get_link(tools_id, device_id)
        if not link:
            return False
        # delete() из BaseCRUD по id, но здесь у нас составной PK — удаляем через filter_by
        # можно воспользоваться filter_by + BaseCRUD.transaction:
        with self.transaction() as db:
            db.query(self.model).filter_by(tools_id=tools_id, device_id=device_id).delete()
        self._cache.clear()
        return True

    def check_tool_belongs_to_device(self, tools_id: int, device_id: int) -> bool:
        """
        Проверяет существование такой связи.
        """
        # Просто проверяем, что get_link не вернул None
        return self.get_link(tools_id, device_id) is not None

    def get_tools_by_device_id(self, device_id: int) -> list[int]:
        """
        Список всех tools_id, связанных с данным device_id.
        """
        links = self.get_by_device_id(device_id)
        return [link.tools_id for link in links]

    def link_tool_to_device(self, tools_id: int, device_id: int) -> bool:
        """
        Создает связь, если её ещё нет.
        :return: True, если добавлена новая связь.
        """
        if not self.check_tool_belongs_to_device(tools_id, device_id):
            return self.add_link(tools_id, device_id)
        return False

    def unlink_tool_from_device(self, tools_id: int, device_id: int) -> bool:
        """
        Удаляет связь, если она существует.
        :return: True, если связь удалена.
        """
        return self.delete_link(tools_id=tools_id, device_id=device_id)

    def this_tool_is_linked(self, tools_id: int) -> bool:
        """
        Проверяет, есть ли в таблице связи для данного инструмента (tools_id).

        :param tools_id: ID инструмента.
        :return: True, если хотя бы одна связь найдена, иначе False.
        """
        # Используем динамический геттер get_by_tools_id
        links = self.get_by_tools_id(tools_id)
        return len(links) > 0
