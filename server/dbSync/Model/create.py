# dbSync/Model/create.py
# from sqlalchemy import create_engine
# from sqlalchemy.exc import IntegrityError
# from dbSync.Engines.CRUD import BaseCRUD
import logging
import os

from dbSync.Engines.CommandEngine import CommandCRUD
from dbSync.Engines.CommandStatusEngine import CommandStatusCRUD

# from docs.docs import CommandCRUD
# from docs.docs import CommandStatusCRUD
logger = logging.getLogger(__name__)
from dbSync.Model.Command import Command
from dbSync.Model.CommandStatus import CommandStatus
from dbSync.Model.Record import Record
from dbSync.Model.SyncConfig import SyncConfig
from dbSync.Model.base import sync_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dbSync.Model import Command


def create_sync_db_file(db_path: str = "sync.db"):
    # Получаем текущую директорию
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Определяем путь к родительской директории  os.path.dirname()
    parent_dir = current_dir + "\\"
    # Формируем полный путь к базе данных в родительской директории
    db_filename = os.path.join(parent_dir, db_path)
    # Проверьте, существует ли файл
    if os.path.exists(db_filename):
        try:
            os.remove(db_filename)
            print(f"Файл '{db_filename}' был успешно удален.")
        except Exception as e:
            print(f"Ошибка при удалении файла: {e}")
    else:
        print(f"Файл '{db_filename}' не найден.")
    try:
        with open(db_filename, 'w') as file:
            file.write('')
        print(f"Файл '{db_filename}' был успешно создан.")
    except Exception as e:
        print(f"Ошибка при создании файла: {e}")
    models = [CommandStatus, Command, Record, SyncConfig]
    engine = create_engine(f'sqlite:///{db_filename}')  # , echo=True
    sync_base.metadata.create_all(engine)
    print(sync_base.metadata.tables.keys())


def demo_status_lifecycle(command_id: int, crud: CommandStatusCRUD):
    """Демонстрация полного жизненного цикла статусов команды"""
    try:
        print(f"\nДемонстрация для команды {command_id}:")

        # Добавляем все возможные статусы по очереди
        statuses = ["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"]

        for status in statuses:
            crud.add_status(command_id, status)
            latest = crud.get_latest_for_command(command_id)
            print(f"Добавлен статус: {latest.status} ({latest.updated_at})")

    except ValueError as e:
        print(f"Ошибка добавления статуса: {str(e)}")
    except Exception as e:
        print(f"Неожиданная ошибка: {str(e)}")


if __name__ == "__main__":
    create_sync_db_file()

    # Инициализация подключения
    engine = create_engine('sqlite:///sync.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Создание CRUD-объекта
    status_crud = CommandStatusCRUD()

    # Создадим тестовые команды (предположим, что CommandCRUD существует)

    command_crud = CommandCRUD()
    test_command_id = command_crud.add(
        table_name="products",
        operation="UPDATE",
        device_number=5
    )

    # Демонстрация жизненного цикла
    demo_status_lifecycle(test_command_id, status_crud)

    # Попытка добавить невалидный статус
    try:
        status_crud.add_status(test_command_id, "INVALID_STATUS")
    except ValueError as e:
        print(f"\nТест ошибки: {str(e)}")
    except RuntimeError as e:
        print(f"\nТест ошибки: {str(e)}")
