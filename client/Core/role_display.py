# -*- coding: utf-8 -*-
"""
Отображаемые названия ролей для UI (локализация).
Соответствует ролям из БД (Create_db) и серверному списку должностей.
"""

# Код роли (name в БД) -> отображаемое название в UI
ROLE_DISPLAY_NAMES = {
    "Developer": "Разработчик",
    "Stockman": "Кладовщик",
    "Admin": "Администратор",
    "Engineer": "Инженер",
    "Manager": "Руководитель",
    "User": "Пользователь",
}


def get_role_display_name(role_name: str) -> str:
    """
    Возвращает отображаемое (переведённое) название роли для UI.
    Если роли нет в словаре, возвращается исходное имя.
    """
    if not role_name:
        return ""
    return ROLE_DISPLAY_NAMES.get(role_name, role_name)
