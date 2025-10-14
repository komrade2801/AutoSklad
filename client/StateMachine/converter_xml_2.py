import xml.etree.ElementTree as ET
import os


def delete_file(file_path):
    # Вычисляем абсолютный путь относительно директории этого файла
    script_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_path = os.path.join(script_dir, file_path)
    if os.path.exists(absolute_path):
        os.remove(absolute_path)
        print(f"File {absolute_path} has been deleted.")
    else:
        print(f"File {absolute_path} does not exist.")


def xml_to_fsm(xml_file):
    # Вычисляем абсолютный путь к xml файлу
    script_dir = os.path.dirname(os.path.abspath(__file__))
    xml_path = os.path.join(script_dir, xml_file)
    tree = ET.parse(xml_path)
    root = tree.getroot()

    states = []
    transitions = []

    # Извлекаем все состояния (узлы)
    for node in root.findall('.//node'):
        states.append({'name': node.attrib['TEXT']})

    # Проходим по узлам и находим переходы (стрелки)
    for node in root.findall('.//node'):
        for arrowlink in node.findall('arrowlink'):
            trigger = arrowlink.get('MIDDLE_LABEL', 'None')  # Триггер, по умолчанию None
            source = node.attrib['TEXT']
            dest_id = arrowlink.get('DESTINATION')
            dest_node = None

            # Ищем узел назначения
            for elem in root.findall('.//node'):
                if elem.get('ID') == dest_id:
                    dest_node = elem
                    break

            if dest_node is not None:
                dest = dest_node.attrib['TEXT']

                # Проверяем направление стрелки (обратная стрелка)
                start_arrow = arrowlink.get('STARTARROW')
                end_arrow = arrowlink.get('ENDARROW')

                if start_arrow == "DEFAULT" and end_arrow == "NONE":
                    # Обратная стрелка, меняем source и dest местами
                    transitions.append({'trigger': trigger, 'source': dest, 'dest': source})
                else:
                    # Прямая стрелка
                    transitions.append({'trigger': trigger, 'source': source, 'dest': dest})

    fsm_dict = {
        'states': states,
        'transitions': transitions
    }
    return fsm_dict


def map_builder():
    # Определяем директорию текущего скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print("Скрипт находится в директории:", script_dir)

    # Путь к xml файлу относительно текущей директории
    xml_file = 'screen.mm'
    delete_file("state_map.py")
    fsm_dict = xml_to_fsm(xml_file)

    # Записываем карту состояний в файл state_map.py (также относительно текущей директории)
    state_map_path = os.path.join(script_dir, "state_map.py")
    with open(state_map_path, 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n\n')
        f.write('from StateMachine.screens import screen\n\n')
        f.write('states = [\n')
        for state in fsm_dict['states']:
            f.write(f"    {{'name': '{state['name']}'}},\n")
        f.write(']\n\n')
        f.write('transitions = [\n')
        for transition in fsm_dict['transitions']:
            f.write(f"    {{'trigger': '{transition['trigger']}', 'source': '{transition['source']}', 'dest': '{transition['dest']}'}},\n")
        f.write(']')
    print("State map saved to state_map.py")


if __name__ == "__main__":
    map_builder()
