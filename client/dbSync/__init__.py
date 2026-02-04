"""
Модуль синхронизации. Состояние «не ставить команды в очередь» хранится по потокам.
"""
import threading

_sync_local = threading.local()


def is_skip_sync_enqueue() -> bool:
    """Возвращает True, если в текущем потоке CRUD не должен ставить команды в очередь (sync/init)."""
    return getattr(_sync_local, "skip_sync_enqueue", False)


def set_skip_sync_enqueue(value: bool) -> None:
    """Устанавливает для текущего потока режим «не ставить команды в очередь»."""
    _sync_local.skip_sync_enqueue = bool(value)
