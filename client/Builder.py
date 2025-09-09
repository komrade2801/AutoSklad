import os
import subprocess

# Задаем необходимые параметры
main_file = "main.py"
output_filename = "my_app"

# Формируем команду Nuitka
command = [
    "nuitka",
    "--standalone",
    "--onefile",
    f"--output-filename={output_filename}",
    main_file
]

# Запускаем команду Nuitka
try:
    subprocess.run(command, check=True)
    print(f"Приложение {output_filename} создано успешно!")
except subprocess.CalledProcessError as e:
    print(f"Ошибка при создании приложения: {e}")




# sudo dpkg --add-architecture i386
#
# wget -nc https://dl.winehq.org/wine-builds/winehq.key
#
# sudo apt-key add winehq.key
#
# sudo add-apt-repository 'deb https://dl.winehq.org/wine-builds/ubuntu/ focal main'
#
# sudo apt install --install-recommends winehq-stable
#
# После выполнения всех этих команд компьютер желательно перезагрузить, команда:
#
# reboot
#
# Когда компьютер перезагрузится проверяем версию wine
#
# wine --version
#
# Должна быть такая "wine-6.0"
# Все команды лучше не набирать с клавиатуры а копировать из этого файла.