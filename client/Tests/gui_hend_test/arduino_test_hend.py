#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import serial

# -------------------------------
# Параметры и настройки
# -------------------------------
# Примерные номера пинов (проверьте соответствие с вашим оборудованием)
SELMODE = 12  # Вход для режима отладки (соединить с GND для входа в настройку)
SDA = 20  # Для LCD I2C (используется библиотека, например, RPLCD)
SCL = 21

# "Аналоговые" входы энкодеров (на Raspberry Pi – цифровые входы, номера могут отличаться)
DTX = 5  # примерный номер (ранее A0)
CLKX = 6  # ранее A1
DTY = 13  # ранее A2
CLKY = 19  # ранее A3
DTZ = 26  # ранее A4
CLKZ = 16  # ранее A5
BTN = 21  # кнопка для пуска моторов при отладке

# Выходы для драйверов шаговых моторов
DIRX = 23  # драйвер X
PULX = 25
DIRY = 27  # драйвер Y
PULY = 29  # обратите внимание: на Raspberry Pi пинов с номером 29 может не быть – выберите доступные

# Концевые выключатели
KONCX = 17  # замените на доступный пин (ранее 53)
KONCY = 18  # ранее 51

# Константы, аналогичные Arduino‑defines
DX = 50  # шагов на щелчок энкодера по X
DY = 50  # по Y
MAXX = 4300
MAXY = 3220
MAXZ = 180
CX = 2000  # координата возврата по X
CY = 1000  # по Y
MULT = 4  # коэффициент микрошагов
CALSP = 1000  # скорость при калибровке
WORKSP = 4000  # рабочая скорость
NUM = 512  # число точек в памяти

# Пример массивов с координатами – здесь для демонстрации просто заполняем числами
Xmass = [i * 10 for i in range(NUM)]
Ymass = [i * 10 for i in range(NUM)]
Zmass = [180 for i in range(NUM)]

# Глобальные переменные
pos = [0, 0, 0]
targ = 0


# -------------------------------
# Классы для периферии
# -------------------------------

# Простейшая имитация шагового двигателя с функциями moveTo() и run()
class StepperMotor:
    def __init__(self, step_pin, dir_pin):
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.position = 0
        self.target = 0
        self.max_speed = WORKSP
        self.acceleration = 10000
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)

    def setAcceleration(self, acc):
        self.acceleration = acc

    def setMaxSpeed(self, speed):
        self.max_speed = speed

    def moveTo(self, target):
        self.target = target
        # определяем направление движения
        direction = GPIO.HIGH if (target > self.position) else GPIO.LOW
        GPIO.output(self.dir_pin, direction)

    def run(self):
        # Простая симуляция: делаем один шаг, если ещё не достигнута цель
        if self.position != self.target:
            step_direction = 1 if self.target > self.position else -1
            self.position += step_direction
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(0.001)  # задержка шага; настройте в зависимости от скорости
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(0.001)
            return True
        return False


# Простейший класс для управления сервоприводом через PWM
class Servo:
    def __init__(self, pin):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, 50)  # 50 Гц
        self.pwm.start(0)

    def write(self, angle):
        # Преобразуем угол в скважность (настройте параметры для вашего серво)
        duty = 2 + (angle / 18)
        self.pwm.ChangeDutyCycle(duty)
        time.sleep(0.3)
        self.pwm.ChangeDutyCycle(0)


# Простейший класс-заглушка для энкодера с кнопкой
class EncoderButton:
    def __init__(self, pin_dt, pin_clk):
        self.pin_dt = pin_dt
        self.pin_clk = pin_clk
        GPIO.setup(self.pin_dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def tick(self):
        # Здесь должна быть логика опроса энкодера
        pass

    def left(self):
        # Вернуть True, если обнаружено движение влево (заглушка)
        return False

    def right(self):
        return False


# Простейший класс для управления LCD (можно заменить на, например, RPLCD)
class LCD:
    def __init__(self):
        # Если у вас установлена библиотека RPLCD, инициализируйте экран там
        # Здесь для примера будем просто выводить в консоль
        pass

    def init(self):
        self.clear()

    def clear(self):
        print("\n" * 5)

    def backlight(self, on=True):
        pass

    def setCursor(self, col, row):
        # Можно реализовать управление положением курсора, если используете реальный LCD
        pass

    def print(self, msg):
        print(msg, end='')


# -------------------------------
# Инициализация объектов
# -------------------------------
# Для LCD можно использовать реальную библиотеку или заглушку:
lcd = LCD()
lcd.init()
lcd.backlight(True)

# Инициализация энкодеров
ebX = EncoderButton(DTX, CLKX)
ebY = EncoderButton(DTY, CLKY)
ebZ = EncoderButton(DTZ, CLKZ)

# Объекты для шаговых моторов и серво
stX = StepperMotor(PULX, DIRX)
stY = StepperMotor(PULY, DIRY)
myservo = Servo(4)  # пин для сервопривода

# Инициализация последовательного порта (настройте порт в зависимости от вашей конфигурации)
ser = serial.Serial('COM29', 9600, timeout=0.1)


# -------------------------------
# Функции, аналогичные Arduino‑функциям
# -------------------------------
def setZero():
    """Калибровка (поиск нуля) по концевым выключателям"""
    global stX, stY
    stX.setMaxSpeed(CALSP)
    stY.setMaxSpeed(CALSP)
    stX.moveTo(-9999999)
    stY.moveTo(-9999999)

    bX = GPIO.input(KONCX)
    bY = GPIO.input(KONCY)
    while bX or bY:
        if bX:
            stX.run()
        if bY:
            stY.run()
        time.sleep(0.001)
        bX = GPIO.input(KONCX)
        bY = GPIO.input(KONCY)
    # Обнуляем позицию
    stX.position = 0
    stY.position = 0
    stX.setMaxSpeed(WORKSP)
    stY.setMaxSpeed(WORKSP)
    print("Калибровка завершена, позиция 0")


def updScreen(n):
    """Обновление отображения координаты на LCD (здесь вывод в консоль)"""
    # Форматируем число с отступами, как в Arduino‑коде
    formatted = f"{pos[n]:4d}"
    print(f"Ось {n}: {formatted}")


def runToPos():
    """Перемещение в заданную позицию"""
    global pos, stX, stY, myservo
    stX.moveTo(pos[0] * MULT)
    stY.moveTo(pos[1] * MULT)
    while stX.run() or stY.run():
        pass
    time.sleep(0.3)
    myservo.write(pos[2])
    time.sleep(0.3)
    myservo.write(180)
    time.sleep(0.3)
    # Отправляем ответ по последовательному порту
    ser.write(b"$2")
    # Возврат в позицию после завершения операции
    stX.moveTo(CX * MULT)
    stY.moveTo(CY * MULT)
    while stX.run() or stY.run():
        pass


def settingMode():
    """Режим отладки с ручной настройкой координат"""
    global pos, stX, stY, myservo, NUM
    lcd.clear()
    lcd.print("X \nY \nZ ")
    updScreen(0)
    updScreen(1)
    updScreen(2)
    setZero()
    while True:
        # Чтение команды из последовательного порта (ожидается число)
        if ser.in_waiting:
            try:
                line = ser.readline().decode().strip()
                p = int(line)
            except Exception as e:
                p = 0
            ser.write(f"{p}\n".encode())
            if p and p <= NUM:
                pos[0] = Xmass[p - 1]
                pos[1] = Ymass[p - 1]
                pos[2] = Zmass[p - 1]
                updScreen(0)
                updScreen(1)
                runToPos()
        # Опрашиваем энкодеры (заглушка – требуется реальная логика)
        ebX.tick()
        ebY.tick()
        ebZ.tick()
        if ebX.left() and pos[0]:
            pos[0] -= DX
            updScreen(0)
        if ebX.right() and pos[0] < MAXX:
            pos[0] += DX
            updScreen(0)
        if ebY.left() and pos[1]:
            pos[1] -= DY
            updScreen(1)
        if ebY.right() and pos[1] < MAXY:
            pos[1] += DY
            updScreen(1)
        if ebZ.left() and pos[2]:
            pos[2] -= 1
            updScreen(2)
        if ebZ.right() and pos[2] < MAXZ:
            pos[2] += 1
            updScreen(2)
        # Если нажата кнопка (BTN), запускаем движение
        if GPIO.input(BTN) == GPIO.LOW:
            stX.moveTo(pos[0] * MULT)
            stY.moveTo(pos[1] * MULT)
            while stX.run() or stY.run():
                pass
            time.sleep(0.3)
            myservo.write(pos[2])
            time.sleep(0.3)
            myservo.write(180)
            time.sleep(0.3)
        time.sleep(0.1)


def main_loop():
    """Основной цикл – приём команды через последовательный порт и выполнение движения"""
    global targ
    while True:
        if ser.in_waiting:
            ch = ser.read().decode()
            if ch == '$':
                time.sleep(0.1)
                targ = 0
                # Считываем оставшиеся символы до символа конца строки
                line = ser.readline().decode()
                for s in line:
                    if s == '\n':
                        if targ and targ <= NUM:
                            pos[0] = Xmass[targ - 1]
                            pos[1] = Ymass[targ - 1]
                            pos[2] = Zmass[targ - 1]
                            runToPos()
                    elif s.isdigit():
                        targ = targ * 10 + int(s)
                ser.write(b"$1")
                print(f"Команда: {targ}")
        time.sleep(0.1)


# -------------------------------
# Главная функция
# -------------------------------
def main():
    global stX, stY, myservo
    GPIO.setmode(GPIO.BCM)  # или GPIO.BOARD – в зависимости от вашей схемы
    # Настройка используемых пинов
    input_pins = [SELMODE, KONCX, KONCY, BTN, DTX, CLKX, DTY, CLKY, DTZ, CLKZ]
    output_pins = [DIRX, PULX, DIRY, PULY, 4]  # 4 – пин для серво
    for pin in input_pins:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    for pin in output_pins:
        GPIO.setup(pin, GPIO.OUT)

    # Инициализация шаговых моторов
    stX.setAcceleration(10000)
    stY.setAcceleration(10000)
    stX.setMaxSpeed(WORKSP)
    stY.setMaxSpeed(WORKSP)

    # Инициализация сервопривода
    myservo.write(180)

    # Если выбран режим настройки (отладки)
    if GPIO.input(SELMODE) == GPIO.LOW:
        settingMode()

    setZero()

    # Перемещаемся в позицию CX, CY
    stX.moveTo(CX * MULT)
    stY.moveTo(CY * MULT)
    while stX.run() or stY.run():
        pass

    lcd.clear()
    lcd.print("Enter pos: ")

    # Основной цикл
    try:
        main_loop()
    except KeyboardInterrupt:
        print("Программа остановлена пользователем.")
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()
