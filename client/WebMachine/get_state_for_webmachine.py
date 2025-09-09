# WebMachine/get_state_for_webmachine.py
import ast
from pathlib import Path

from StateMachine.state_map import transitions, states


def load_state_map(file_path):
    """
    Загружает states и transitions из файла state_map.py.
    """

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Извлечение states и transitions с помощью ast
    module = ast.parse(content)
    states = []
    transitions = []

    for node in module.body:
        if isinstance(node, ast.Assign):
            if node.targets[0].id == "states":
                states = ast.literal_eval(node.value)
            elif node.targets[0].id == "transitions":
                transitions = ast.literal_eval(node.value)

    return states, transitions

def filter_http_related(states, transitions):
    """
    Фильтрует states и transitions, оставляя только те, что связаны с "http".
    """
    # Фильтрация states
    web_states = [state for state in states if "http" in state["name"]]

    # Фильтрация transitions
    web_transitions = [
        t for t in transitions
        if "http" in t["source"] or "http" in t["dest"]
    ]

    return web_states, web_transitions

def save_web_state_map(file_path, states, transitions):
    """
    Сохраняет отфильтрованные states и transitions в файл web_state_map.py.
    """
    separator = ",\\n\\t"  # строка, которая буквально содержит \t\n
    # Формирование содержимого файла
    file_content = f'''# -*- coding: utf-8 -*-
    
    states = [
        {separator.join(f"{{'name': '{s['name']}'}}" for s in states)}
    ]
    
    transitions = [
        {separator.join(f"{{'trigger': '{t['trigger']}', 'source': '{t['source']}', 'dest': '{t['dest']}'}}" for t in transitions)}
    ]
    '''

    # Запись в файл
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(file_content)

def generate_web_state_map():
    """
    Основная функция: загружает, фильтрует и сохраняет данные.
    """
    # Пути к файлам
    # state_map_path = Path("StateMachine\state_map.py")
    # web_state_map_path = Path("WebMachine\web_state_map.py")
    #
    # Получаем директорию, где находится этот скрипт
    current_dir = Path(__file__).resolve().parent
    # Строим путь к файлу state_map.py относительно корня проекта
    state_map_path = current_dir.parent / "StateMachine" / "state_map.py"
    web_state_map_path = current_dir / "web_state_map.py"

    # Загрузка данных
    states, transitions = load_state_map(state_map_path)

    # Фильтрация данных
    web_states, web_transitions = filter_http_related(states, transitions)

    # Сохранение данных
    save_web_state_map(web_state_map_path, web_states, web_transitions)

    print(f"Файл {web_state_map_path} успешно создан.")

# Запуск функции
if __name__ == "__main__":
    generate_web_state_map()