# dbSync/Engines/RecordEngine.py
"""
Модуль для работы с записями данных синхронизации

Содержит CRUD-класс для управления записями данных, связанными с командами синхронизации.
Обеспечивает хранение и управление сериализованными данными для операций CREATE/UPDATE.
"""
import threading
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc #, text
from sqlalchemy.exc import IntegrityError
import json
import logging
from dbSync.Engines.CRUD import BaseCRUD
logger = logging.getLogger(__name__)
from dbSync.Model.Record import Record


class RecordCRUD(BaseCRUD):
    """
    CRUD-класс для работы с записями данных синхронизации

    Наследует базовый функционал CRUD-операций и добавляет специализированные методы
    для работы с сериализованными данными команд. Работает с моделью Record.

    Атрибуты:
        session (Session): SQLAlchemy сессия для работы с БД
        model (Type[Record]): Модель данных записей синхронизации
    """

    def __init__(self, session: Session=None, *, cache_maxsize: int = 1000, cache_ttl: int = 300):
        """
        Инициализация CRUD-объекта для записей данных

        :param session: Объект SQLAlchemy сессии
        :param cache_maxsize: Максимальный размер кеша (по умолчанию 1000)
        :param cache_ttl: Время жизни кеша в секундах (по умолчанию 300)
        """
        super().__init__(session=session, model=Record, cache_maxsize=cache_maxsize, cache_ttl=cache_ttl)

    def add_record(self, command_id: int, data: Dict[str, Any]) -> bool:
        """
        Добавляет новую запись данных для команды синхронизации

        :param command_id: ID связанной команды синхронизации
        :param data: Данные для сериализации в JSON
        :return: True при успешном добавлении, иначе False

        Пример:
            crud.add_record(123, {"price": 199})
            True
        """
        try:
            logger.debug("[RecordEngine][add_record] command_id: %s, data: %s", command_id, data)
            return self.add(
                command_id=command_id,
                data_json=json.dumps(data, ensure_ascii=False),
                last_modified=datetime.utcnow()
            )
        except (IntegrityError, TypeError, ValueError) as e:
            logger.exception("[RecordEngine][add_record] IntegrityError: %s", e)
            self.session.rollback()
            error_msg = f"Ошибка добавления записи: {str(e)}"
            raise ValueError(error_msg) from e

    def update_data(self, record_id: int, new_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные в существующей записи

        :param record_id: ID обновляемой записи
        :param new_data: Новые данные для сериализации
        :return: True при успешном обновлении

        Пример:
            crud.update_data(5, {"price": 299})
            True
        """
        try:
            logger.debug("[RecordEngine][update_data] record_id: %s, new_data: %s", record_id, new_data)
            return self.update(
                record_id,
                data_json=json.dumps(new_data, ensure_ascii=False),
                last_modified=datetime.utcnow()
            )
        except (IntegrityError, TypeError, ValueError) as e:
            logger.exception("[RecordEngine][update_data] IntegrityError: %s", e)
            self.session.rollback()
            error_msg = f"Ошибка обновления записи: {str(e)}"
            raise ValueError(error_msg) from e

    def get_json_data(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Возвращает десериализованные данные записи

        :param record_id: ID запрашиваемой записи
        :return: Десериализованные данные или None

        Пример:
            data = crud.get_json_data(5)
            logger.(data)
            {"price": 199}
        """
        record = self.get(record_id)
        if record and record.data_json:
            try:
                logger.debug("[RecordEngine][get_json_data] record_id: %s", record_id)
                return json.loads(record.data_json)
            except json.JSONDecodeError as e:
                logger.exception("[RecordEngine][get_json_data] JSONDecodeError: %s", e)
                return None
        return None

    def get_by_command(self, command_id: int) -> List[Record]:
        """
        Возвращает все записи данных для указанной команды

        :param command_id: ID команды синхронизации
        :return: Список объектов Record

        Пример:
            records = crud.get_by_command(123)
            [r.id for r in records]
            [5, 6, 7]
        """
        logger.debug("[RecordEngine][get_by_command] command_id: %s", command_id)
        return self.filter_by(command_id=command_id).order_by(Record.last_modified).all()

    def get_last_for_command(self, command_id: int) -> Optional[Record]:
        """
        Возвращает последнюю запись данных для команды

        :param command_id: ID команды синхронизации
        :return: Объект Record или None

        Пример:
            record = crud.get_last_for_command(123)
            logger.(record.last_modified)
            2023-01-01 12:00:00
        """
        logger.debug("[RecordEngine][get_last_for_command] command_id: %s", command_id)
        return (
            self.filter_by(command_id=command_id)
            .order_by(desc(Record.last_modified))
            .limit(1)
            .first()
        )

    def validate_json(self, record_id: int) -> bool:
        """
        Проверяет валидность JSON данных в записи

        :param record_id: ID проверяемой записи
        :return: True если данные валидны

        Пример:
            crud.validate_json(5)
            True
        """
        logger.debug("[RecordEngine][validate_json] record_id: %s", record_id)
        record = self.get(record_id)
        if not record or not record.data_json:
            return False

        try:
            json.loads(record.data_json)
            return True
        except json.JSONDecodeError as e:
            logger.exception("[RecordEngine][validate_json] JSONDecodeError: %s", e)
            return False

    def get_bulk_records(self, command_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Получает сериализованные данные по списку команд.

        :param command_ids: список идентификаторов команд
        :return: словарь {command_id: распарсенные данные}
        """
        logger.debug("[RecordEngine][get_bulk_records] command_ids: %s", command_ids)

        result = {}
        if not command_ids:
            return result

        try:
            with self.transaction() as db:
                records = (
                    db.query(self.model)
                    .filter(self.model.command_id.in_(command_ids))
                    .order_by(self.model.command_id, desc(self.model.last_modified))
                    .all()
                )

            for record in records:
                # если в списке есть дубликаты по command_id — выбираем последнюю запись
                if record.command_id not in result:
                    try:
                        result[record.command_id] = json.loads(record.data_json or "{}")
                    except json.JSONDecodeError:
                        logger.warning("[RecordEngine][get_bulk_records] Ошибка JSON в записи id=%s", record.id)
                        result[record.command_id] = {}

            return result

        except Exception as e:
            logger.exception("[RecordEngine][get_bulk_records] %s", e)
            raise
