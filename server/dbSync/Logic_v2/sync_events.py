# sync_events.py
# Глобальный реестр коллбэков для событий после вставки
from typing import Dict, List, Callable, Any

_after_insert_listeners: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}


def register_after_insert(table: str, fn: Callable[[Dict[str, Any]], None]) -> None:
    """
    Регистрирует функцию-слушатель, вызываемую после вставки в таблицу `table`.
    """
    _after_insert_listeners.setdefault(table, []).append(fn)


def fire_after_insert(table: str, record: Dict[str, Any]) -> None:
    """
    Вызывает всех зарегистрированных слушателей для таблицы `table`.
    :param table: имя таблицы, в которую вставлена запись
    :param record: словарь с данными вставленной записи
    """
    for fn in _after_insert_listeners.get(table, []):
        try:
            fn(record)
        except Exception:
            import traceback
            traceback.print_exc()
