import os
import traceback
from Core.app_logging import get_logger

logger = get_logger(__name__)


def find_btn_objects(folder_path):
    """
    Находит все уникальные названия объектов, начинающиеся с "btn_", в файлах,
    имена которых начинаются с "screen_" или "widget_", в заданной папке.
    Возвращает словарь, где ключом является имя файла,
    а значением - список уникальных названий объектов.

    Args:
        folder_path (str): Путь к папке, в которой нужно искать файлы.

    Returns:
        dict: Словарь, где ключом является имя файла, а значением - список уникальных названий объектов.
    """
    btn_objects = {}

    for filename in os.listdir(folder_path):
        if (filename.startswith("screen_") or filename.startswith("widget_")) and filename.endswith(".py"):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    unique_btn_objects = set()
                    for line in file:
                        for word in line.split():
                            if "btn_" in word:
                                if word.startswith("btn_"):
                                    unique_btn_objects.add(word)
                                else:
                                    # Пытаемся найти объект, содержащий "btn_" в середине
                                    for subword in word.split("."):
                                        if subword.startswith("btn_"):
                                            unique_btn_objects.add(subword)
                    if unique_btn_objects:
                        btn_objects[filename] = list(unique_btn_objects)
            except UnicodeDecodeError:
                logger.exception("Ошибка при чтении файла %s. Пропускаем его.", filename)
                continue

    return btn_objects


if __name__ == "__main__":
    # Укажите путь к папке, в которой нужно искать файлы
    folder_path = "/GUI"

    btn_objects_dict = find_btn_objects(folder_path)
    logger.info("screen = %s", {fn.split(".")[0]: objs for fn, objs in btn_objects_dict.items()})
