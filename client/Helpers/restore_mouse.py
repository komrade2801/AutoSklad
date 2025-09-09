import os
import subprocess

# Находим все подключенные мыши
devices = subprocess.check_output(['xinput', 'list'], universal_newlines=True)
device_names = [line.split('=')[1].split()[0] for line in devices.splitlines() if 'pointer' in line]

# Восстанавливаем настройки для каждой найденной мыши
for device in device_names:
    subprocess.call(['xinput', 'set-prop', device, 'Coordinate Transformation Matrix', '1', '0', '0', '0', '1', '0', '0', '0', '1'])
    print(f"Настройки мыши '{device}' восстановлены.")

print("Готово!")