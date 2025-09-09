
def setmode(BCM):
    print("Настройка режима")
    BCM()


def BCM():
    print("Включен режим BCM")


def OUT():
    print("Включена настройка пина на выход")


def LOW():
    print("Включен низкий уровень")

def HIGH():
    print("Включен высокий уровень")

def setup(pin, setting):
    print(f"Выбран пин: №{pin}")
    setting()

def output(pin, setting):
    print(f"Выбран пин: №{pin}")
    setting()

