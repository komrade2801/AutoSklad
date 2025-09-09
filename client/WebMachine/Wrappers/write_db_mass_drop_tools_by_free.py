"""

write_db_mass_drop_tools_by_free
Пример формата JSON

JSON-файл должен содержать два ключа:

    "tools_data" – список объектов, каждый из которых представляет данные для создания объекта Tools.
    "cells_data" – список объектов, каждый из которых представляет данные для создания объекта Cell.


{
  "tools_data": [
    {
      "id": 1,
      "name": "Tool A",
      "plan_id": null,
      "Tools_groups_id": 2,
      "description": "Описание инструмента A",
      "img": "image_a.png"
    },
    {
      "id": 2,
      "name": "Tool B",
      "plan_id": null,
      "Tools_groups_id": 2,
      "description": "Описание инструмента B",
      "img": "image_b.png"
    }
  ],
  "cells_data": [
    {
      "id": 1,
      "Tools_id": 1,
      "Tools_groups_id": 2,
      "Status_id": 1,
      "number": 101
    },
    {
      "id": 2,
      "Tools_id": 2,
      "Tools_groups_id": 2,
      "Status_id": 1,
      "number": 102
    }
  ]
}

"""




import json
from typing import List
from DB.Models.Tools import Tools
from DB.Models.Cell import Cell
from datetime import datetime


def parse_tools(data: List[dict]) -> List[Tools]:
    tools_list = []
    for item in data:
        # Здесь можно добавить преобразование или валидацию данных
        tool = Tools(
            id=item.get("id"),
            name=item.get("name"),
            plan_id=item.get("plan_id"),
            Tools_groups_id=item.get("Tools_groups_id"),
            description=item.get("description"),
            img=item.get("img")
        )
        tools_list.append(tool)
    return tools_list


def parse_cells(data: List[dict]) -> List[Cell]:
    cells_list = []
    for item in data:
        cell = Cell(
            id=item.get("id"),
            Tools_id=item.get("Tools_id"),
            Tools_groups_id=item.get("Tools_groups_id"),
            Status_id=item.get("Status_id"),
            number=item.get("number")
        )
        cells_list.append(cell)
    return cells_list


def process_mass_drop_tools_by_free(json_input: str, engine_object) -> bool:
    """
    Обёртка, которая принимает JSON-строку, парсит данные,
    преобразует их в списки объектов Tools и Cell,
    и вызывает исходную функцию write_db_mass_drop_tools_by_free.
    """
    try:
        data = json.loads(json_input)
        tools_data = parse_tools(data.get("tools_data", []))
        cells_data = parse_cells(data.get("cells_data", []))
    except Exception as e:
        raise ValueError("Ошибка парсинга JSON: " + str(e))

    # Вызываем исходную функцию с полученными данными.
    # engine_object – объект, у которого есть метод write_db_mass_drop_tools_by_free
    return engine_object.write_db_mass_drop_tools_by_free(tools_data, cells_data)


# Пример использования:
if __name__ == "__main__":
    # Пример JSON-строки, полученной из файла или запроса
    sample_json = '''{
      "tools_data": [
        {"id": 1, "name": "Tool A", "plan_id": null, "Tools_groups_id": 2, "description": "Описание A", "img": "img_a.png"},
        {"id": 2, "name": "Tool B", "plan_id": null, "Tools_groups_id": 2, "description": "Описание B", "img": "img_b.png"}
      ],
      "cells_data": [
        {"id": 1, "Tools_id": 1, "Tools_groups_id": 2, "Status_id": 1, "number": 101},
        {"id": 2, "Tools_id": 2, "Tools_groups_id": 2, "Status_id": 1, "number": 102}
      ]
    }'''

    # Предположим, engine_object – это экземпляр класса, где реализована функция write_db_mass_drop_tools_by_free
    # Например, engine_object = ActionMapper(executor) (как в вашем клиентском коде)
    # result = process_mass_drop_tools_by_free(sample_json, engine_object)
    # print("Result:", result)
