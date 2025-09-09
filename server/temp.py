import re

def camel_to_snake(name: str) -> str:
    """
    Переводит строку из CamelCase (или PascalCase) в snake_case.
    Например:
      "MassLoad"  -> "mass_load"
      "XMLParser" -> "xml_parser"
    """
    # Шаг 1: вставляем подчёркивание перед каждой заглавной буквой (кроме самой первой)
    s1 = re.sub(r'(?<!^)(?=[A-Z])', '_', name)
    # Шаг 2: приводим всё к нижнему регистру
    return s1.lower()

def normalize_to_snake(s: str) -> str:
    """
    Если строка уже содержит '_', просто приводим к lowercase.
    Иначе считаем, что это CamelCase/PascalCase и конвертируем.
    """
    if "_" in s:
        return s.lower()
    else:
        return camel_to_snake(s)

a = "MassLoad"
b = "mass_load"

print(camel_to_snake(a))  # -> "mass_load"
print(normalize_to_snake(b))  # -> "mass_load"

if normalize_to_snake(a) == normalize_to_snake(b):
    print("Они совпадают после приведения к snake_case")
else:
    print("Не совпадают")
