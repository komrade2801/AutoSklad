import os


def get_files_in_current_folder():
    """
    Возвращает список файлов, находящихся в той же папке, где находится скрипт.

    Returns:
        list: Список файлов в папке.
    """
    # Получаем путь к текущей директории
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Получаем список файлов в текущей директории
    files = os.listdir(current_dir)

    return files


if __name__ == "__main__":
    files = get_files_in_current_folder()
    print("Files in the current folder:", files)