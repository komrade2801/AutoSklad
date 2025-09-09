# dbSync/Engines/SyncConfigEngine.py
"""
Модуль для работы с конфигурацией синхронизации таблиц

Содержит CRUD-класс для управления настройками синхронизации различных таблиц в системе.
Позволяет включать/отключать синхронизацию для конкретных таблиц и проверять текущий статус.
"""

from typing import Optional

from dbSync.Engines.CRUD import BaseCRUD
# from docs.docs import BaseCRUD
from dbSync.Model.SyncConfig import SyncConfig


class SyncConfigCRUD(BaseCRUD):
    """
    Класс для управления конфигурацией синхронизации таблиц

    Наследует базовый функционал CRUD-операций и добавляет специализированные методы
    для работы с настройками синхронизации. Работает с моделью SyncConfig.

    Атрибуты:
        session (Session): SQLAlchemy сессия для работы с БД
        model (Type[SyncConfig]): Модель данных для конфигурации синхронизации
    """

    def __init__(self, session=None):
        """
        Инициализация CRUD-объекта для конфигурации синхронизации

        :param session: Объект SQLAlchemy сессии
        """
        super().__init__(session=session, model=SyncConfig)

    def enable_sync(self, table_name: str) -> bool:
        """
        Включает синхронизацию для указанной таблицы

        :param table_name: Название таблицы для активации синхронизации
        :return: True если операция выполнена успешно, иначе False
        """
        return self._update_or_create(table_name, True)

    def disable_sync(self, table_name: str) -> bool:
        """
        Отключает синхронизацию для указанной таблицы

        :param table_name: Название таблицы для деактивации синхронизации
        :return: True если операция выполнена успешно, иначе False
        """
        return self._update_or_create(table_name, False)

    def get_status(self, table_name: str) -> Optional[bool]:
        """
        Получает текущий статус синхронизации для таблицы

        :param table_name: Название таблицы для проверки
        :return: Состояние синхронизации (True/False) или None если запись не найдена
        """
        # tables = self.all()
        # [print(f"[SyncConfigCRUD][get_status] найдено среди всех: ", table.table_name) for table in tables]
        # Получаем список всех конфигураций для таблицы
        configs = self.filter_by(table_name=table_name)
        # print(f"[SyncConfigCRUD][get_status]Поиск SyncConfig для table="{table_name}" → найденный: {configs!r}")

        # Берем первую запись если существует
        config = configs[0] if configs else None

        return config.enabled if config else None

    def _update_or_create(self, table_name: str, status: bool) -> bool:
        """
        Внутренний метод для обновления или создания записи

        :param table_name: Название таблицы для изменения
        :param status: Новый статус синхронизации
        :return: Результат выполнения операции (True/False)
        """
        # Поиск существующей конфигурации
        configs = self.filter_by(table_name=table_name)
        config = configs[0] if configs else None

        if config:
            # Обновление существующей записи
            return self.update(config.table_name, **{"enabled": status})

        # Создание новой записи если не найдено
        return self.add(table_name=table_name, enabled=status)


# # Пример использования:
# if __name__ == "__main__":
#     from sqlalchemy import create_engine
#     from sqlalchemy.orm import sessionmaker
#
#     # Инициализация сессии
#     engine = create_engine("sqlite:///sync.db")
#     Session = sessionmaker(bind=engine)
#     session = Session()
#
#     # Создание CRUD-объекта
#     sync_crud = SyncConfigCRUD()
#
#     # Включение синхронизации для таблицы
#     sync_crud.enable_sync("products")
#
#     # Проверка статуса
#     status = sync_crud.get_status("products")
#     logger.(f"Синхронизация для products: {"включена" if status else "отключена"}")