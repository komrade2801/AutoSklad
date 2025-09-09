from EventsSystem.action_db import ActionMapper
from StateMachine.state_map import transitions


class StateRouter:
    def __init__(self, mappers):
        """
        Инициализация StateRouter.

        Transitions: Список переходов, определяющих логику переходов между состояниями.
        :param mappers: Словарь с экземплярами ActionMapper, где ключ — имя модуля.
        """
        self.transitions = transitions
        self.action_mappers = mappers
        self.current_state = None

    def set_initial_state(self, state):
        """
        Устанавливает начальное состояние.

        :param state: Имя состояния.
        """
        self.current_state = state

    def route(self, trigger, module_name, action, *args, **kwargs):
        """
        Выполняет маршрут на основании триггера и текущего состояния.

        :param trigger: Причина перехода.
        :param module_name: Имя модуля, в котором необходимо выполнить действие.
        :param action: Действие, которое необходимо выполнить в модуле.
        :param args: Дополнительные позиционные аргументы для действия.
        :param kwargs: Дополнительные именованные аргументы для действия.
        :return: Результат выполнения действия./*************************************
        """
        if not self.current_state:
            raise ValueError("Текущее состояние не установлено. Используйте 'set_initial_state' для его определения.")

        # Выполняем действие в соответствующем модуле
        if module_name not in self.action_mappers:
            raise ValueError(f"Модуль '{module_name}' не зарегистрирован в картографах действий.")

        mapper = self.action_mappers[module_name]
        result = mapper.execute(action, *args, **kwargs)

        # Определяем следующее состояние на основе карты переходов
        next_state = None
        for transition in self.transitions:
            if transition['trigger'] == trigger and transition['source'] == self.current_state:
                next_state = transition['dest']
                break

        if not next_state:
            raise ValueError(f"Не найдено допустимого перехода для триггера '{trigger}' из состояние '{self.current_state}'.")

        # Лог текущего перехода
        print(f"Переход: {self.current_state} -> {next_state} (триггер: {trigger})")

        # Обновляем текущее состояние
        self.current_state = next_state

        return result


    def find_transition_trigger(self, start, current, value, fallback_function=None):
        """
        Определяет триггер перехода между состояниями с учётом контекста начального состояния.

        Алгоритм приоритетов:
        1. Переходы из текущего состояния
        2. Уникальный переход или идентичные дубликаты
        3. Соответствие префиксам назначения (текущий → начальный)
        4. Fallback-разрешение неоднозначности
        5. Первый доступный переход

        :param start: Исходное состояние (например, 'screen_1_welcome')
        :param current: Текущее состояние (например, 'read_db_help')
        :param value: Контекстные данные для fallback
        :param fallback_function: Функция обработки неоднозначности
        :return: Название триггера или результат fallback-функции
        """
        # Извлечение префиксов для контекстной фильтрации
        start_prefix = start.split('_', 1)[0]
        current_prefix = current.split('_', 1)[0]

        # Фильтрация переходов из текущего состояния
        transitions = [t for t in self.transitions if t['source'] == current]

        # Случай 1: Нет доступных переходов
        if not transitions:
            return fallback_function([], value) if fallback_function else None

        # Случай 2: Единственный переход
        if len(transitions) == 1:
            return transitions[0]['trigger']

        # Случай 3: Все переходы идентичны
        if all(t == transitions[0] for t in transitions[1:]):
            return transitions[0]['trigger']

        # Случай 4: Фильтрация по приоритетным префиксам
        for prefix in [current_prefix, start_prefix]:
            candidates = [t for t in transitions if t['dest'].startswith(prefix)]
            if not candidates:
                continue

            # Найдены кандидаты
            if len(candidates) == 1:
                return candidates[0]['trigger']

            # Обработка неоднозначности
            if fallback_function:
                result = fallback_function(candidates, value)
                return self._parse_fallback_result(result)

            return candidates[0]['trigger']

        # Случай 5: Общий fallback
        if fallback_function:
            result = fallback_function(transitions, value)
            return self._parse_fallback_result(result)

        return transitions[0]['trigger']

    def _parse_fallback_result(self, result):
        """Вспомогательный метод для обработки результатов fallback-функции"""
        if isinstance(result, dict):
            return result.get('trigger')
        if isinstance(result, list) and result:
            return result[0].get('trigger')
        return result


    # def find_transition_trigger(self, start, current, value, fallback_function=None):
    #     """
    #     Находит триггер перехода из текущей точки в конечную точку на основе начальной точки.
    #
    #     :param start: Начальная точка (например, 'screen_1_welcome').
    #     :param current: Текущая точка (например, 'read_db_help').
    #     :param fallback_function: Функция, вызываемая в случае неоднозначности (если после фильтрации остается несколько вариантов).
    #     :return: Строка с названием триггера или результат работы fallback_function.
    #     """
    #     # Извлекаем первое слово из начальной точки
    #     start_prefix = start.split('_')[0]
    #     current_prefix = current.split('_')[0]
    #     # Фильтруем переходы по текущей точке в source
    #     filtered_transitions = [t for t in self.transitions if t['source'] == current]
    #     if len(filtered_transitions) == 1:
    #         # Если найден один подходящий переход, возвращаем его триггер
    #         return filtered_transitions[0]['trigger']
    #
    #     filtered_transitions_is_quality = False
    #     transition_back = {}
    #     for transition in filtered_transitions:
    #         if transition_back != {}:
    #             filtered_transitions_is_quality = (transition['trigger'] == transition_back['trigger'])
    #             filtered_transitions_is_quality = filtered_transitions_is_quality and (transition['dest'] == transition_back['dest'])
    #             filtered_transitions_is_quality = filtered_transitions_is_quality and (transition['source'] == transition_back['source'])
    #         transition_back = transition
    #     if filtered_transitions_is_quality:
    #         return filtered_transitions[0]['trigger']
    #
    #     matching_transitions = []
    #     for prefix in [current_prefix, start_prefix]:
    #         # Дополнительно фильтруем по начальному слову из start в dest
    #         matching_transitions = [t for t in filtered_transitions if t['dest'].startswith(prefix)]
    #         if matching_transitions:
    #             break
    #
    #     if len(matching_transitions) == 1:
    #         # Если найден один подходящий переход, возвращаем его триггер
    #         return matching_transitions[0]['trigger']
    #
    #     elif len(matching_transitions) > 1 and fallback_function:
    #         # Если есть несколько подходящих переходов, вызываем fallback_function
    #         return fallback_function(matching_transitions, value)
    #
    #     # Если подходящих переходов нет, возвращаем None или результат fallback_function, если она есть
    #     transition = filtered_transitions if not fallback_function else fallback_function(matching_transitions, value)
    #     if not transition:
    #         # Если подходящих переходов нет, возвращаем None или результат fallback_function, если она есть
    #         transition = filtered_transitions[0]['trigger']
    #
    #     if transition:
    #         if isinstance(transition, dict):
    #             return transition
    #         elif isinstance(transition, list):
    #             return transition[0]['trigger']
    #     return None


# Пример fallback-функции для обработки неоднозначных случаев
def example_fallback(transitions):
    print("Неоднозначность в выборе перехода:")
    for t in transitions:
        print(t)
    return "unknown_trigger"  # Возвращаем значение по умолчанию


# # Пример использования StateRouter
# if __name__ == "__main__":
#     # Определяем карту переходов
#     transitions = [
#         {'trigger': 'btn_login', 'source': 'screen_3_authorization', 'dest': 'read_db_authorization'},
#         {'trigger': 'view_type_admin', 'source': 'read_db_authorization', 'dest': 'screen_26_admin'},
#         {'trigger': 'type_storekeeper', 'source': 'read_db_authorization', 'dest': 'screen_14_stockman'},
#         # Дополнительно можно добавить другие переходы
#     ]
#
#     # Создаем модули с ActionMapper
#     db_mapper = ActionMapper()
#     action_mappers = {
#         "DB": db_mapper
#     }
#
#     # Инициализируем StateRouter
#     router = StateRouter(transitions, action_mappers)
#     router.set_initial_state("screen_3_authorization")
#
#     # Выполняем переходы
#     login_result = router.route("btn_login", "DB", "read_db_authorization", "admin", "password123")
#     if login_result and login_result.get("type") == "admin":
#         router.route("view_type_admin", "DB", "write_log", "Admin logged in.")
#     elif login_result:
#         router.route("type_storekeeper", "DB", "write_log", "Stockman logged in.")


# Пример использования метода find_transition_trigger
if __name__ == "__main__":
    # Создаем модули с ActionMapper
    db_mapper = ActionMapper()
    action_mappers = {
        "db": db_mapper
    }

    # Инициализируем StateRouter
    router = StateRouter(action_mappers)
    router.set_initial_state("screen_3_authorization")

    # Определяем начальную и текущую точки
    start = "screen_14_stockman"
    current = router.current_state

    # Пример fallback-функции
    def resolve_ambiguity(matching_transitions):
        print("Обнаружена неоднозначность!")
        for t in matching_transitions:
            print(f"Триггер: {t['trigger']}, Source: {t['source']}, Dest: {t['dest']}")
        # Возвращаем первый триггер в случае неоднозначности
        return matching_transitions[0]['trigger']

    # Пытаемся найти триггер
    trigger = router.find_transition_trigger(
        start=start,
        current=current,
        fallback_function=resolve_ambiguity
    )

    if trigger:
        print(f"Найден триггер: {trigger}")
        # Выполняем переход
        result = router.route(trigger, "DB", "some_action", param="example")
        print(f"Результат выполнения: {result}")
    else:
        print("Триггер не найден. Переход невозможен.")
