import os
import pickle
from pathlib import Path

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

from DB.Data.base import Base  # ваш Base, где прописаны модели


def rebuild_with_backup(db_url: str, base_metadata, backup_folder: str = "tmp_backup"):
    """
    1) Читает все существующие таблицы в базе данных.
    2) Резервирует их содержимое в папке backup_folder (*.pkl).
    3) Дропает все таблицы.
    4) Создаёт все таблицы заново по base_metadata.
    5) Восстанавливает данные, вставляя только совпадающие колонки.
    """
    # 0. Настройка движка и сессии
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 1. Рефлектим текущее состояние БД
    old_meta = MetaData()
    old_meta.reflect(bind=engine)

    # Создаём папку для резервов
    os.makedirs(backup_folder, exist_ok=True)

    # 2. Резерв таблиц
    for tbl_name, tbl in old_meta.tables.items():
        rows = session.execute(tbl.select()).fetchall()
        cols = [c.name for c in tbl.columns]
        with open(os.path.join(backup_folder, f"{tbl_name}.pkl"), "wb") as f:
            pickle.dump((cols, rows), f)

    # 3. Дроп и ресоздание по новым моделям
    base_metadata.drop_all(engine)
    base_metadata.create_all(engine)

    # 4. Восстановление данных
    new_meta = MetaData()
    new_meta.reflect(bind=engine)

    for tbl_name, tbl in new_meta.tables.items():
        backup_path = os.path.join(backup_folder, f"{tbl_name}.pkl")
        if not os.path.exists(backup_path):
            # Нет резервной копии → пропускаем
            continue

        # Загружаем резерв
        with open(backup_path, "rb") as f:
            cols, rows = pickle.load(f)

        # Оставляем только те колонки, что есть сейчас в таблице
        valid_cols = [c for c in cols if c in tbl.c]
        if not valid_cols:
            continue

        # Строим список dict для вставки
        to_insert = []
        for row in rows:
            row_dict = dict(zip(cols, row))
            filtered = {col: row_dict[col] for col in valid_cols}
            to_insert.append(filtered)

        # Пакетная вставка
        if to_insert:
            # engine.execute(tbl.insert(), to_insert)
            with engine.connect() as conn:
                conn.execute(tbl.insert(), to_insert)
                conn.commit()

    session.close()


def rebuild_db():
    """
    Удаляет файл SQLite, если он есть, создаёт пустой,
    затем запускает rebuild_with_backup.
    """
    # Путь к файлу БД (например, SQLite)
    current_dir = Path(__file__).parent / "Data"
    from options import db_path
    db_file = current_dir / db_path
    db_url = f"sqlite:///{db_file}"

    # Удаляем старый файл
    if db_file.exists():
        db_file.unlink()

    # Гарантируем, что папка существует
    current_dir.mkdir(parents=True, exist_ok=True)
    # Создаём пустой файл
    db_file.write_text("")

    # Вызываем процедуру с бэкапом
    rebuild_with_backup(db_url, Base.metadata, backup_folder=str(current_dir / "backup"))

    print("Database rebuild complete with data restored.")


if __name__ == "__main__":
    rebuild_db()
