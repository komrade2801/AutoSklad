import sys
import platform


def detect_platform() -> str:
    """
    Определяет платформу выполнения кода.
    Возвращает одно из значений:
    - 'Windows'
    - 'macOS'
    - 'Raspberry Pi'
    - 'Linux' (другие дистрибутивы)
    - 'Unknown'
    """
    # Определяем базовую ОС
    os_name = platform.system()

    if os_name == 'Windows':
        return 'Windows'

    if os_name == 'Darwin':
        return 'macOS'

    if os_name == 'Linux':
        # Проверяем, является ли устройство Raspberry Pi
        try:
            # Способ 1: Через модель устройства
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                if 'raspberry pi' in model.lower():
                    return 'Raspberry Pi'
        except FileNotFoundError:
            pass

        try:
            # Способ 2: Через информацию о процессоре
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'raspberry pi' in cpuinfo.lower():
                    return 'Raspberry Pi'
        except FileNotFoundError:
            pass

        return 'Linux'

    return 'Unknown'


if __name__ == "__main__":
    current_platform = detect_platform()
    print(f"Текущая платформа: {current_platform}")
    print(f"Дополнительная информация:")
    print(f"- Python version: {platform.python_version()}")
    print(f"- OS name: {platform.system()}")
    print(f"- Platform: {sys.platform}")