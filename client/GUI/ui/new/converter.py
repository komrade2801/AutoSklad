# import os
# import subprocess
#
#
# def convert_ui_to_py(ui_folder):
#     for filename in os.listdir(ui_folder):
#         if filename.endswith(".ui"):
#             ui_file = os.path.join(ui_folder, filename)
#             py_file = os.path.join(ui_folder, f"{os.path.splitext(filename)[0]}.py")
#             subprocess.run(["pyuic5", "-o", py_file, ui_file])
#             print(f"Converted {ui_file} to {py_file}")
#
#
# if __name__ == "__main__":
#     # Получаем путь текущей директории
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     convert_ui_to_py(current_dir)
#


import os
import subprocess
import re

def convert_ui_to_py(ui_folder):
    for filename in os.listdir(ui_folder):
        if filename.endswith(".ui"):
            ui_file = os.path.join(ui_folder, filename)
            new_filename = f"{re.sub(r'/d+_', '', os.path.splitext(filename)[0])}.py"
            py_file = os.path.join(ui_folder, new_filename)
            subprocess.run(["pyuic5", "-o", new_filename, filename])
            print(f"Converted {ui_file} to {new_filename}")

if __name__ == "__main__":
    # Получаем путь текущей директории
    current_dir = os.path.dirname(os.path.abspath(__file__))
    convert_ui_to_py(current_dir)