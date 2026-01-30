# dbSync/Engines/CommandEngine.py
"""
Модуль для работы с командами синхронизации

Содержит CRUD-класс для управления командами синхронизации между сервером и устройствами.
Обеспечивает полный жизненный цикл команд: создание, обновление, подтверждение выполнения.
"""
import logging
import threading
import traceback
from datetime import datetime
from typing import Optional, Dict, Any  # List,
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from dbSync.Engines.CRUD import BaseCRUD
from dbSync.Engines.CommandStatusEngine import CommandStatusCRUD
from dbSync.Engines.RecordEngine import RecordCRUD

from dbSync.Model.Command import Command
from dbSync.Model.CommandStatus import CommandStatus
from dbSync.Model.Record import Record

# from dbSync.Runner import create_db_session

logger = logging.getLogger(__name__)


class CommandCRUD(BaseCRUD):
    """
    CRUD-класс для работы с командами синхронизации

    Наследует базовый функционал CRUD-операций и добавляет специализированные методы
    для управления жизненным циклом команд. Работает с моделью Command.

    Атрибуты:
        session (Session): SQLAlchemy сессия для работы с БД
        model (Type[Command]): Модель данных команд синхронизации
    """

    def __init__(self,
                 *,
                 session: Session = None,
                 cache_maxsize: int = 1000,
                 cache_ttl: int = 300
                 ):
        """
        Инициализация CRUD-объекта для команд синхронизации

        :param session: Объект SQLAlchemy сессии
        :param cache_maxsize: Максимальный размер кеша (по умолчанию 1000)
        :param cache_ttl: Время жизни кеша в секундах (по умолчанию 300)
        """
        super().__init__(session=session, model=Command, cache_maxsize=cache_maxsize, cache_ttl=cache_ttl)

    def add_command(self,
                    table_name: str,
                    operation: str,
                    record_id: int,
                    device_number: int,
                    data_json: str) -> int:
        """
        Создаёт новую команду с начальным статусом PENDING и связанной записью

        :param table_name: Название целевой таблицы (max 50 символов)
        :param operation: Тип операции (CREATE/UPDATE/DELETE)
        :param record_id: ID связанной записи в исходной таблице
        :param device_number: Числовой идентификатор устройства-получателя
        :param data_json: JSON-сериализованные данные для синхронизации
        :return: ID созданной команды

        Исключения:
            ValueError: При нарушении ограничений целостности данных
            RuntimeError: При ошибках базы данных

        Пример использования:
            try:
                cmd_id = crud.add_command(
                    table_name="products",
                    operation="UPDATE",
                    record_id=123,
                    device_number=5,
                    data_json="{"price": 199.0}"
                )
                logger.(f"Создана команда ID: {cmd_id}")
            except ValueError as e:
                logger.(f"Ошибка создания команды: {str(e)}")
        """
        try:
            logger.debug("[CommandEngine][add_command] начало создание команды")
            with self.transaction() as db:
                # Создаем основную команду
                cmd = self.model(
                    table_name=table_name[:50],  # Обеспечение ограничения длины
                    operation=operation,
                    record_id=record_id,
                    device_number=device_number,
                    created_at=datetime.utcnow()
                )
                super().add(**cmd.to_dict())  # Используем базовый метод добавления

                # Создаем связанные сущности через их CRUD-классы
                RecordCRUD().add(
                    command_id=cmd.id,
                    data_json=data_json
                )

                CommandStatusCRUD().add(
                    command_id=cmd.id,
                    status="PENDING"
                )
                logger.debug("[CommandEngine][add_command] команда создана, id=%s", cmd.id)
                return cmd.id

        except IntegrityError as e:
            self.session.rollback()
            error_msg = f"Ошибка целостности данных: {str(e)}"
            logger.exception("[CommandEngine][add_command] IntegrityError: %s", e)

            raise ValueError(error_msg) from e

        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = f"Ошибка базы данных: {str(e)}"
            logger.exception("[CommandEngine][add_command] SQLAlchemyError: %s", e)
            raise RuntimeError(error_msg) from e

        finally:
            logger.debug("[CommandEngine][add_command] очистка кеша")
            self._cache.clear()

    def update_command(self, cmd_id: int, **kwargs) -> bool:
        """
        Обновляет поля существующей команды

        :param cmd_id: ID обновляемой команды
        :param kwargs: Поля и новые значения для обновления
        :return: True при успешном обновлении

        Пример:
            crud.update_command(42, operation="DELETE")
            True
        """
        result = super().update(cmd_id, **kwargs)
        self._cache.clear()
        logger.debug("[CommandEngine][update_command] команда обновлена")
        return result

    def delete_command(self, cmd_id: int) -> bool:
        """
        Удаляет команду и все связанные с ней данные

        :param cmd_id: ID удаляемой команды
        :return: True при успешном удалении

        Пример:
            crud.delete_command(42)
            True
        """
        result = super().delete(cmd_id)
        self._cache.clear()
        logger.debug("[CommandEngine][delete_command] команда удалена")
        return result

    def acknowledge(self, cmd_id: int, new_status: str = "COMPLETED") -> bool:
        """
        Обновляет статус выполнения команды

        :param cmd_id: ID команды
        :param new_status: Новый статус (COMPLETED/FAILED/IN_PROGRESS)
        :return: True при успешном обновлении

        Исключения:
            ValueError: При недопустимом статусе или неверном ID команды
            RuntimeError: При ошибках базы данных

        Пример использования:
            try:
                success = crud.acknowledge(42, "COMPLETED")
                logger.(success)  # True
            except ValueError as e:
                logger.(f"Ошибка данных: {e}")
            except RuntimeError as e:
                logger.(f"Ошибка базы данных: {e}")
        """
        if new_status not in {"PENDING", "COMPLETED", "FAILED", "IN_PROGRESS"}:
            raise ValueError(f"Недопустимый статус: {new_status}")

        try:
            # Используем метод add из CoreEngine
            self.add(
                command_id=cmd_id,
                status=new_status,
                updated_at=datetime.utcnow()
            )
            logger.debug("[CommandEngine][acknowledge] статус обновлен")
            return True

        except IntegrityError as e:
            logger.exception("[CommandEngine][acknowledge] IntegrityError: %s", e)
            raise ValueError(f"Неверный ID команды: {cmd_id}") from e

        except SQLAlchemyError as e:
            logger.exception("[CommandEngine][acknowledge] SQLAlchemyError: %s", e)
            raise RuntimeError(f"Ошибка базы данных: {str(e)}") from e

    def get_pending_for_device(self, device_number: int):
        cache_key = self._make_key("pending_for_device", device_number)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            cache_key = self._make_key("pending_for_device", device_number)
            if cache_key in self._cache:
                return self._cache[cache_key]

            # 1) Подзапрос: самый свежий статус каждой команды
            subquery = (
                self.session.query(CommandStatus.command_id,
                                   func.max(CommandStatus.updated_at).label("max_updated"))
                .group_by(CommandStatus.command_id)
                .subquery()
            )

            # 2) Фильтры для основного запроса
            joins = [subquery, CommandStatus]
            filters = [
                Command.id == subquery.c.command_id,
                CommandStatus.command_id == subquery.c.command_id,
                CommandStatus.updated_at == subquery.c.max_updated,
                CommandStatus.status == "PENDING",
                Command.device_number == device_number
            ]

            # 3) Используем новый метод
            _pending = self.join_filter_order(
                joins=joins,
                filters=filters,
                order_by=desc(Command.created_at)
            )

            # Кэшируем вручную (или внутри join_filter_order)
            self._cache[cache_key] = _pending
            return _pending

        except SQLAlchemyError as e:
            # Откатываем транзакцию и пробрасываем ошибку
            self.session.rollback()
            raise RuntimeError(f"Database error: {e}") from e

    def get_command_details(self, cmd_id: int) -> Optional[Dict[str, Any]]:
        """
        Возвращает полную информацию о команде с данными и статусами

        :param cmd_id: ID команды
        :return: Словарь с данными команды или None

        Пример:
            details = crud.get_command_details(42)
            details.keys()
            dict_keys(["command", "record", "statuses"])
        """
        with self.transaction() as db:
            command = db.query(Command).get(cmd_id)
            if not command:
                logger.debug("[CommandEngine][get_command_details] команда не найдена: cmd_id=%s", cmd_id)
                return None

            record = db.query(Record).filter_by(command_id=cmd_id).first()
            statuses = db.query(CommandStatus).filter_by(command_id=cmd_id).all()
            logger.debug("[CommandEngine][get_command_details] команда получена: cmd_id=%s", cmd_id)

            return {
                "command": command,
                "record": record,
                "statuses": statuses
            }
