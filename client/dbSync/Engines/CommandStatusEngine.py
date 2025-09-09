# dbSync/Engines/CommandStatusEngine.py
"""
Модуль для работы со статусами команд синхронизации

Содержит CRUD-класс для управления статусами выполнения команд синхронизации.
Обеспечивает отслеживание жизненного цикла команд и их текущего состояния.
"""
import logging
import threading
import traceback
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from dbSync.Engines.CRUD import BaseCRUD
from dbSync.Model.CommandStatus import CommandStatus
from dbSync.constants import CommandStatusEnum

# from dbSync.Runner import create_db_session

logger = logging.getLogger(__name__)
# VALID_STATUSES = {"PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"}
VALID_STATUSES = set(CommandStatusEnum.values())

class CommandStatusCRUD(BaseCRUD):
    """
    CRUD-класс для работы со статусами команд синхронизации

    Наследует базовый функционал CRUD-операций и добавляет специализированные методы
    для управления жизненным циклом команд. Работает с моделью CommandStatus.

    Атрибуты:
        session (Session): SQLAlchemy сессия для работы с БД
        model (Type[CommandStatus]): Модель данных статусов команд
    """

    def __init__(self, session: Session = None, *, cache_maxsize: int = 1000, cache_ttl: int = 300):
        """
        Инициализация CRUD-объекта для статусов команд

        :param session: Объект SQLAlchemy сессии
        :param cache_maxsize: Максимальный размер кеша (по умолчанию 1000)
        :param cache_ttl: Время жизни кеша в секундах (по умолчанию 300)
        """
        super().__init__(session=session, model=CommandStatus, cache_maxsize=cache_maxsize, cache_ttl=cache_ttl)

    def add_status(self, command_id: int, status: str) -> bool:
        """
        Добавляет новый статус для команды синхронизации

        :param command_id: ID связанной команды синхронизации
        :param status: Новый статус из допустимых значений:
                      PENDING, IN_PROGRESS, COMPLETED, FAILED
        :return: True при успешном добавлении, иначе ValueError
        """
        # 0) жёсткая валидация до обращения к БД
        if status not in VALID_STATUSES:
            raise ValueError(f"Недопустимый статус: {status!r}")

        try:
            print(
                f"[ПОТОК][{threading.current_thread().name}]"
                f"[CommandStatusEngine][add_status][INFO] "
                f"- command_id: {command_id}, status: {status}. [{datetime.now()}]"
            )
            return super().add(
                command_id=command_id,
                status=status,
                updated_at=datetime.utcnow()
            )
        except IntegrityError as e:
            # сюда уже не попадёт CHECK-ошибка из-за неправильного status,
            # но мы всё равно отлавливаем другие возможные нарушения целостности
            print(
                f"[ПОТОК][{threading.current_thread().name}]"
                f"[CommandStatusEngine][add_status][ERROR][IntegrityError] "
                f"- error: {e}, подробности: - {traceback.format_exc()}. [{datetime.now()}]"
            )
            self.session.rollback()
            raise ValueError(f"Ошибка при добавлении статуса: {e}") from e

    def update_status(self, status_id: int, new_status: str) -> bool:
        """
        Обновляет статус команды

        :param status_id: ID записи статуса
        :param new_status: Новое значение статуса
        :return: True при успешном обновлении, иначе False

        Пример:
            crud.update_status(5, "COMPLETED")
            True
        """
        result = super().update(status_id, status=new_status)
        self._cache.clear()
        print(f"[ПОТОК][{threading.current_thread().name}][CommandStatusEngine][update_status][INFO] - status_id: {status_id}, new_status: {new_status}. [{datetime.now()}]")
        return result

    def delete_status(self, status_id: int) -> bool:
        """
        Удаляет запись статуса по ID

        :param status_id: ID удаляемого статуса
        :return: True при успешном удалении, иначе False

        Пример:
            crud.delete_status(5)
            True
        """
        result = super().delete(status_id)
        self._cache.clear()
        print(f"[ПОТОК][{threading.current_thread().name}][CommandStatusEngine][delete_status][INFO] - status_id: {status_id}. [{datetime.now()}]")
        return result

    def query_by_command(self, command_id: int):
        # возвращает SQLAlchemy Query, а не список
        print(f"[ПОТОК][{threading.current_thread().name}][CommandStatusEngine][query_by_command][INFO] - command_id: {command_id}. [{datetime.now()}]")
        return self.session.query(self.model).filter_by(command_id=command_id)

    def get_by_command_id(self, command_id: int) -> List[CommandStatus]:
        """
        Возвращает историю статусов для команды в хронологическом порядке

        :param command_id: ID команды синхронизации
        :return: Список объектов CommandStatus

        Пример:
            statuses = crud.get_by_command_id(123)
            [s.status for s in statuses]
            ["PENDING", "COMPLETED"]
        """
        print(f"[ПОТОК][{threading.current_thread().name}][CommandStatusEngine][get_by_command_id][INFO] - command_id: {command_id}. [{datetime.now()}]")
        # filter_by теперь отдаёт Query, поэтому можно вызывать order_by() и затем all()
        return (
            self.session
            .query(CommandStatus)
            .filter_by(command_id=command_id)
            .order_by(CommandStatus.updated_at)
            .all()
        )

    def get_latest_for_command(self, command_id: int) -> Optional[CommandStatus]:
        """
        Возвращает последний зарегистрированный статус для команды

        :param command_id: ID команды синхронизации
        :return: Объект CommandStatus или None если статусов нет

        Пример:
            latest = crud.get_latest_for_command(123)
            latest.status
            "COMPLETED"
        """
        print(f"[ПОТОК][{threading.current_thread().name}][CommandStatusEngine][get_latest_for_command][INFO] - command_id: {command_id}. [{datetime.now()}]")
        return (
            self.session
            .query(CommandStatus)
            .filter_by(command_id=command_id)
            .order_by(desc(CommandStatus.updated_at))
            .limit(1)
            .one_or_none()
        )

    def get_pending(self) -> List[CommandStatus]:
        """
        Возвращает все ожидающие обработки статусы (PENDING)

        :return: Список объектов CommandStatus

        Пример:
            pending = crud.get_pending()
            len(pending)
            3
        """
        print(f"[ПОТОК][{threading.current_thread().name}][CommandStatusEngine][get_pending][INFO] - [{datetime.now()}]")
        return self.get_by_status("PENDING")

    def get_failed(self) -> List[CommandStatus]:
        """
        Возвращает все неудачные выполнения команд (FAILED)

        :return: Список объектов CommandStatus

        Пример:
            failed = crud.get_failed()
            len(failed)
            2
        """
        print(f"[ПОТОК][{threading.current_thread().name}][CommandStatusEngine][get_failed][INFO] - [{datetime.now()}]")
        return self.get_by_status("FAILED")

    def get_completed(self) -> List[CommandStatus]:
        """
        Возвращает все успешно выполненные команды (COMPLETED)

        :return: Список объектов CommandStatus

        Пример:
            completed = crud.get_completed()
            len(completed)
            15
        """
        print(f"[ПОТОК][{threading.current_thread().name}][CommandStatusEngine][get_completed][INFO] - [{datetime.now()}]")
        return self.get_by_status("COMPLETED")

    def get_active(self) -> List[CommandStatus]:
        """
        Возвращает все выполняющиеся в данный момент команды (IN_PROGRESS)

        :return: Список объектов CommandStatus

        Пример:
            active = crud.get_active()
            len(active)
            2
        """
        print(f"[ПОТОК][{threading.current_thread().name}][CommandStatusEngine][get_active][INFO] - [{datetime.now()}]")
        return self.get_by_status("IN_PROGRESS")
