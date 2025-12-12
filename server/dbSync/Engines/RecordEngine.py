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

# from docs.docs import BaseCRUD
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
            print(f"[ПОТОК][{threading.current_thread().name}][RecordEngine][add_record][INFO] - command_id: {command_id}, data: {data}. [{datetime.now()}]")
            return self.add(
                command_id=command_id,
                data_json=json.dumps(data, ensure_ascii=False),
                last_modified=datetime.utcnow()
            )
        except (IntegrityError, TypeError, ValueError) as e:
            print(f"[ПОТОК][{threading.current_thread().name}][RecordEngine][add_record][ERROR][IntegrityError] - error: {e}, подробности: - {traceback.format_exc()}. [{datetime.now()}]")
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
            print(f"[ПОТОК][{threading.current_thread().name}][RecordEngine][update_data][INFO] - record_id: {record_id}, new_data: {new_data}. [{datetime.now()}]")
            return self.update(
                record_id,
                data_json=json.dumps(new_data, ensure_ascii=False),
                last_modified=datetime.utcnow()
            )
        except (IntegrityError, TypeError, ValueError) as e:
            print(f"[ПОТОК][{threading.current_thread().name}][RecordEngine][update_data][ERROR][IntegrityError] - error: {e}, подробности: - {traceback.format_exc()}. [{datetime.now()}]")
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
                print(f"[ПОТОК][{threading.current_thread().name}][RecordEngine][get_json_data][INFO] - record_id: {record_id}. [{datetime.now()}]")
                return json.loads(record.data_json)
            except json.JSONDecodeError:
                print(f"[ПОТОК][{threading.current_thread().name}][RecordEngine][get_json_data][ERROR][JSONDecodeError] - error: {e}, подробности: - {traceback.format_exc()}. [{datetime.now()}]")
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
        print(f"[ПОТОК][{threading.current_thread().name}][RecordEngine][get_by_command][INFO] - command_id: {command_id}. [{datetime.now()}]")
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
        print(f"[ПОТОК][{threading.current_thread().name}][RecordEngine][get_last_for_command][INFO] - command_id: {command_id}. [{datetime.now()}]")
        return (
            self.session.query(self.model)
            .filter_by(command_id=command_id)
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
        print(f"[ПОТОК][{threading.current_thread().name}][RecordEngine][validate_json][INFO] - record_id: {record_id}. [{datetime.now()}]")
        record = self.get(record_id)
        if not record or not record.data_json:
            return False

        try:
            json.loads(record.data_json)
            return True
        except json.JSONDecodeError:
            print(f"[ПОТОК][{threading.current_thread().name}][RecordEngine][validate_json][ERROR][JSONDecodeError] - error: {e}, подробности: - {traceback.format_exc()}. [{datetime.now()}]")
            return False

    def get_bulk_records(self, command_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Получает сериализованные данные по списку команд.

        :param command_ids: список идентификаторов команд
        :return: словарь {command_id: распарсенные данные}
        """
        print(f"[ПОТОК][{threading.current_thread().name}][RecordEngine][get_bulk_records][INFO] - command_ids: {command_ids}. [{datetime.now()}]")

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
                        print(f"[RecordEngine][get_bulk_records][ERROR] Ошибка JSON в записи id={record.id}")
                        result[record.command_id] = {}

            return result

        except Exception as e:
            print(f"[RecordEngine][get_bulk_records][ERROR] - {e}, подробности: - {traceback.format_exc()}")
            raise


# Пример использования
if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Инициализация подключения
    engine = create_engine("sqlite:///sync.db")
    Session = sessionmaker(bind=engine)
    session = Session()

    # Создание CRUD-объекта
    record_crud = RecordCRUD()

    # Добавление новой записи
    try:
        record_crud.add_record(
            command_id=1,
            data={"product": "Coffee", "price": 199}
        )
        print("Запись успешно добавлена")
    except ValueError as e:
        print(f"Ошибка: {str(e)}")

    # Получение данных
    data = record_crud.get_json_data(1)
    print(f"Данные записи: {data}")