from Helpers.Singleton import singleton


@singleton
class Handlers:
    def __init__(self):
        """
        Инициализация хранилища обработчиков событий.
        """
        self.event_handlers = {}

    def clear(self):
        """
        Очищает все зарегистрированные обработчики событий.
        """
        self.event_handlers = {}

    def register(self, event: str, func: callable):
        """
        Регистрирует обработчик для указанного события.
        :param event: Имя события (строка).
        :param func: Функция-обработчик (вызываемая).
        """
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(func)

    def dispatch(self, event: str, *args, **kwargs):
        """
        Вызывает все обработчики, зарегистрированные для события.
        :param event: Имя события (строка).
        :param args: Позиционные аргументы для обработчиков.
        :param kwargs: Именованные аргументы для обработчиков.
        """
        handlers = self.event_handlers.get(event)
        if handlers is None:
            raise ValueError(f"Неизвестное событие '{event}'.")

        for func in handlers:
            func(*args, **kwargs)

    def remove_handler(self, event: str, func: callable):
        """
        Удаляет указанный обработчик для события.
        :param event: Имя события (строка).
        :param func: Функция-обработчик (вызываемая).
        """
        handlers = self.event_handlers.get(event)
        if handlers is None:
            raise ValueError(f"Неизвестное событие '{event}'.")

        try:
            handlers.remove(func)
            if not handlers:
                del self.event_handlers[event]
        except ValueError:
            raise ValueError(f"Обработчик не найден для события '{event}'.")

    def has_event(self, event: str) -> bool:
        """
        Проверяет, зарегистрированы ли обработчики для события.
        :param event: Имя события (строка).
        :return: True, если обработчики для события существуют, иначе False.
        """
        return event in self.event_handlers


# Пример использования
if __name__ == "__main__":
    handlers_instance = Handlers()


    # Определяем несколько функций-обработчиков
    def on_event_a(data):
        print(f"Событие A вызвано с данными: {data}")


    def on_event_b(data):
        print(f"Событие B вызвано с данными: {data}")


    # Регистрируем обработчики событий
    handlers_instance.register('event_a', on_event_a)
    handlers_instance.register('event_b', on_event_b)

    # Вызываем обработчики событий
    handlers_instance.dispatch('event_a', {'ключ': 'значение'})
    handlers_instance.dispatch('event_b', [1, 2, 3])

    # Проверяем наличие события
    print(handlers_instance.has_event('event_a'))  # True

    # Удаляем обработчик события
    handlers_instance.remove_handler('event_a', on_event_a)

    # Попытка вызвать удалённое событие вызовет исключение
    try:
        handlers_instance.dispatch('event_a', {'ключ': 'значение'})
    except ValueError as e:
        print(e)  # Выводит: Неизвестное событие 'event_a'.
