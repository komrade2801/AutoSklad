import os


def merge_python_files(src_dir: str, out_path: str, encoding: str = 'utf-8') -> None:
    """
    Сливает весь код из .py-файлов в папке src_dir (рекурсивно) в один файл out_path.

    :param src_dir: путь к каталогу, в котором ищем .py-файлы
    :param out_path: путь к итоговому файлу, который будет создан/перезаписан
    :param encoding: кодировка для чтения и записи (по умолчанию 'utf-8')
    """
    with open(out_path, 'w', encoding=encoding) as out_f:
        for root, _, files in os.walk(src_dir):
            # сортируем имена, чтобы порядок был детерминирован
            for fname in sorted(files):
                if not fname.endswith('.py'):
                    continue
                full_path = os.path.join(root, fname)
                # пишем заголовок раздела
                rel_path = os.path.relpath(full_path, src_dir)
                out_f.write(f'# ===== File: {rel_path} =====\n')
                try:
                    with open(full_path, 'r', encoding=encoding) as in_f:
                        out_f.write(in_f.read())
                except Exception as e:
                    out_f.write(f'# ** Ошибка чтения {rel_path}: {e}\n')
                out_f.write('\n\n')
    print(f'Слияние завершено: все .py-файлы из `{src_dir}` записаны в `{out_path}`')


if __name__ == '__main__':
    # например, слить весь код из папки "src" в файл "logic.py"
    merge_python_files(src_dir='dbSync', out_path='dbSync.py')
