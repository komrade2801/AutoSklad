"""
Эмуляция модуля RPi.GPIO для тестирования.
Реализует базовые функции: setmode, setup, output, input, PWM, cleanup и т.д.
"""

# Глобальные словари для хранения конфигурации пинов и их состояния
_pin_modes = {}
_pin_values = {}
_mode = None

# Константы
BCM = "BCM"
BOARD = "BOARD"
IN = 0
OUT = 1
HIGH = 1
LOW = 0
PUD_UP = 1

class GPIO:
    # Для удобства можно обращаться к константам через класс
    BCM = BCM
    BOARD = BOARD
    IN = IN
    OUT = OUT
    HIGH = HIGH
    LOW = LOW
    PUD_UP = PUD_UP

def setmode(mode):
    """Устанавливает режим нумерации пинов (BCM или BOARD)."""
    global _mode
    _mode = mode
    print(f"GPIO: Режим установлен: {mode}")

def setup(pin, mode, pull_up_down=None):
    """
    Настраивает пин в режиме ввода или вывода.
    Если для входа указан pull_up_down==PUD_UP, пину присваивается значение HIGH по умолчанию.
    """
    _pin_modes[pin] = mode
    if mode == OUT:
        _pin_values[pin] = LOW
    elif mode == IN:
        _pin_values[pin] = HIGH if pull_up_down == PUD_UP else LOW
    print(f"GPIO: Пин {pin} настроен как {'OUT' if mode==OUT else 'IN'} с pull_up_down={pull_up_down}")

def output(pin, value):
    """
    Устанавливает значение пина (только для пинов, настроенных как OUT).
    """
    if pin not in _pin_modes or _pin_modes[pin] != OUT:
        raise RuntimeError(f"GPIO: Пин {pin} не настроен как выход")
    _pin_values[pin] = value
    print(f"GPIO: Выходной пин {pin} установлен в значение {value}")

def input(pin):
    """
    Возвращает текущее значение пина (если пин не настроен — возвращает LOW).
    """
    val = _pin_values.get(pin, LOW)
    print(f"GPIO: Чтение пина {pin}: {val}")
    return val

def cleanup():
    """
    Сбрасывает настройки всех пинов и режим нумерации.
    """
    global _pin_modes, _pin_values, _mode
    _pin_modes.clear()
    _pin_values.clear()
    _mode = None
    print("GPIO: cleanup выполнен")

class PWM:
    """
    Эмуляция PWM-класса.
    """
    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = 0
        setup(pin, OUT)
        print(f"PWM: Инициализирован на пине {pin} с частотой {frequency} Гц")

    def start(self, duty_cycle):
        """Запускает PWM с заданным коэффициентом заполнения (duty cycle)."""
        self.duty_cycle = duty_cycle
        output(self.pin, duty_cycle)
        print(f"PWM: Запущен на пине {self.pin} с duty cycle {duty_cycle}%")

    def ChangeDutyCycle(self, duty_cycle):
        """Изменяет коэффициент заполнения PWM."""
        self.duty_cycle = duty_cycle
        output(self.pin, duty_cycle)
        print(f"PWM: На пине {self.pin} duty cycle изменён на {duty_cycle}%")

    def stop(self):
        """Останавливает PWM."""
        self.duty_cycle = 0
        output(self.pin, LOW)
        print(f"PWM: Остановлен на пине {self.pin}")

# Если требуется функция PWM (как в оригинальном файле)
def PWM_func(pin, frequency):
    return PWM(pin, frequency)

# Реализация функций-констант (если необходимы в виде функций)
def OUT_func():
    return OUT

def HIGH_func():
    return HIGH

def LOW_func():
    return LOW

def IN_func():
    return IN

def PUD_UP_func():
    return PUD_UP

if __name__ == '__main__':
    # Для совместимости с исходным кодом, где функции объявлены, но не реализованы:
    setmode(BCM)
    setup(4, OUT)           # пример настройки пина 4 как выхода
    output(4, HIGH)         # установка пина 4 в HIGH
    value = input(4)        # чтение значения пина 4
    pwm = PWM_func(18, 50)  # создание PWM на пине 18 с частотой 50 Гц
    pwm.start(70)           # запуск PWM с 70% заполнением
    pwm.ChangeDutyCycle(50) # изменение заполнения на 50%
    pwm.stop()              # остановка PWM
    cleanup()
