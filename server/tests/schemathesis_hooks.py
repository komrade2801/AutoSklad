import schemathesis

# Игнорируемые пути (регулярные выражения)
IGNORE_PATHS = [
    r".*delete.*",
    r".*remove.*",
    r".*drop.*",
    r".*unlink.*"
]

# Фиксированные значения для ID
FIXED_IDS = {
    "device_id": 1,
    "user_id": 1,
    "role_id": 1,
    "right_id": 1,
    "tool_id": 1,
    "cell_id": 1,
    "plan_id": 1
}


@schemathesis.hook
def before_generate_path_parameters(context, strategy):
    """Фиксирует идентификаторы в параметрах путей"""

    def fix_ids(params):
        # Пропускаем опасные эндпоинты
        if any(pattern in context.operation.path for pattern in IGNORE_PATHS):
            return params

        # Заменяем все известные ID на фиксированные значения
        for param_name, fixed_value in FIXED_IDS.items():
            if param_name in params:
                params[param_name] = fixed_value
        return params

    return strategy.map(fix_ids)


@schemathesis.hook
def before_generate_query(context, strategy):
    """Фиксирует идентификаторы в query-параметрах"""

    def fix_query(query):
        # Пропускаем опасные эндпоинты
        if any(pattern in context.operation.path for pattern in IGNORE_PATHS):
            return query

        # Заменяем ID в query-параметрах
        for param_name, fixed_value in FIXED_IDS.items():
            if param_name in query:
                query[param_name] = fixed_value
        return query

    return strategy.map(fix_query)