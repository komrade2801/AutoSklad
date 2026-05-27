
//$RGB,180,255,30 Задать цвет адресной ленте
//$LOCK Открыть замок
//$LED,1 Включить ленту 1, выключить 0
//$SOL Дёрнуть соленоид
//$ZERO Все моторы в ноль
//$ZERO,3 Указанный мотор в ноль
//$MOT,0,0,0,0,0 Моторы 1-5 в позиции через запятую. Если не надо двигать, то надо отправить старую позицию
//$MOT,15000,15000,25400,23700,1150 Макс корды
//$g Запустить выдачу всех ячеек подряд
//$c, Задать номер выдаваемой ячейки
//$f Выдать одну ячейку
//$STOP Останавливает выдачу всех ячеек после завершения выдачи текущей


#include <AccelStepper.h> // https://downloads.arduino.cc/libraries/github.com/waspinator/AccelStepper-1.64.0.zip
#include <microLED.h>     // https://github.com/GyverLibs/microLED/archive/refs/heads/main.zip


microLED<30, 10, MLED_NO_CLOCK, LED_WS2818, ORDER_GRB, CLI_AVER> strip;  // Количество светодиодов, ножка
const byte konc[] = {3, 4, 5, 0, 1, 2}; // Номера портов PC у концевиков 0-5
long pos[5];                            // Позиции моторов
const byte inv[] = {0, 0, 0, 0, 0};     // Инвертирование направления моторов 1-5. Если 1, то инвертирован
AccelStepper motor[] = {
  AccelStepper(1, 2, 12),
  AccelStepper(1, 3, 12),
  AccelStepper(1, 4, 12),
  AccelStepper(1, 5, 12),
  AccelStepper(1, 6, 12)
};

bool motorsMoving = false;      // Флаг: выполняется ли движение
byte runMotFlags = 0;           // Какие моторы ещё движутся (аналог runMot из motRun)
float targetPos[5];              // Целевые позиции (сохраняем между вызовами)

// Состояние для неблокирующего ZERO
bool zeroActive = false;         // Выполняется ли калибровка
byte zeroStep = 0;               // Текущий этап (0..много)
byte zeroMotorIdx = 0;           // Какой мотор обрабатываем (2,3,4, затем 1 для пары)
byte zeroSubStep = 0;            // Для пары моторов (0 и 1) – подэтапы
unsigned long zeroLastTime = 0;  // Не нужен, т.к. работаем без задержек
// Для одиночной калибровки (команда $ZERO,<n>)
bool zeroSingleActive = false;
byte zeroSingleMotor = 0;    // 0..4
byte zeroSingleStep = 0;

bool motorErrorFlag = false;   // был ли сбой концевика при движении

uint16_t shReg; // Состояние регистра

int16_t cordZ[] = {417, 328, 228, 117, -2};  // корды рядов
float shift;
uint16_t row, count;
float shiftX;
bool go, zapret;
uint8_t steps;

uint32_t timer_lock;                               // Таймер замка
uint32_t timer_lock0;
bool ind_l;
uint32_t timer_sol_lock;                           // Таймер соленоида
uint32_t timer_sol_lock0;
bool ind_s;

void setup() {
  Serial.begin(9600);
  pinMode(9, OUTPUT); //CLK
  pinMode(7, OUTPUT); // DATA
  pinMode(8, OUTPUT); // LATCH
  setOuts();

  for (byte i = 0; i < 5; i++) {
    motor[i].setAcceleration(3000);
    motor[i].setMaxSpeed(2000);
  }

  strip.clear();
  strip.setBrightness(100);
  strip.set(0, mRGB(255, 255, 255));
  strip.show();
}

void loop() {
  if (Serial.available()) {
    if (Serial.read() == '$') {
      String str = Serial.readStringUntil('\n');

      if (str.startsWith("RGB,")) {           // Если команда адресной ленты
        str = str.substring(4);
        byte r = str.substring(0, str.indexOf(",")).toInt();
        str = str.substring(str.indexOf(",") + 1);
        byte g = str.substring(0, str.indexOf(",")).toInt();
        str = str.substring(str.indexOf(",") + 1);
        byte b = str.toInt();
        for (byte i = 0; i < 30; i++)
          strip.set(i, mRGB(r, g, b));
        strip.show();
        Serial.println("DONE");
        return;
      }

      if (str.startsWith("LOCK,")) {                      // Если команда открытия замка
        uint32_t timer_l = str.substring(5).toInt();     // Получение подстроки начиная с запятой и преобразование в int
        //delay(st);
        timer_lock = timer_l;
        timer_lock0 = millis();
        shReg |= (1 << 2); setOuts();
        ind_l = HIGH;
        return;
      }

      if (str.startsWith("LED,")) {             // Если команда вкл/выкл ленты
        byte st = str.substring(4).toInt();     // Получение подстроки начиная с запятой и преобразование в int
        if (st < 2) {                           // Если значение 0 или 1
          if (st) shReg |= (1 << 3);            // Включение
          else shReg &= ~(1 << 3);              // Выключение
          setOuts();
          Serial.println("DONE");
        } else Serial.println("ERROR");         // Если значение с ошибкой
        return;
      }

      if (str.startsWith("SOL,")) {             // Если команда соленоида
        uint32_t timer_s = str.substring(4).toInt();              // Получение подстроки начиная с запятой и преобразование в int
        timer_sol_lock = timer_s;
        timer_sol_lock0 = millis();
        shReg |= (1 << 4); setOuts();
        ind_s = HIGH;
        return;
      }

      if (str.startsWith("c,")) {             // Если команда соленоида
        uint16_t st = str.substring(2).toInt();     // Получение подстроки начиная с запятой и преобразование в int
        st--;
        count = st;
        Serial.print("ячейка ");
        Serial.println(count + 1);
        return;
      }

      if (str == "ZERO") {
        // Если уже движется MOT или другой ZERO, ответ BUSY
        if (motorsMoving || zeroActive) {
          Serial.println("BUSY");
          return;
        }
        Serial.println("WAIT");
        // Инициализация автомата
        zeroActive = true;
        zeroStep = 0;
        zeroMotorIdx = 4;    // начало с мотора 5
        zeroSubStep = 0;
        return;
      }

      else if (str.startsWith("ZERO,")) {
        String numStr = str.substring(5);
        byte motorNum = numStr.toInt();
        motorNum--;
        if (motorNum < 0 || motorNum > 4) {
          Serial.println("ERROR");
          return;
        }
        // Проверка, не занят ли контроллер другим движением
        if (motorsMoving || zeroActive || zeroSingleActive) {
          Serial.println("BUSY");
          return;
        }
        // Запуск одиночной калибровки
        zeroSingleActive = true;
        zeroSingleMotor = motorNum;
        zeroSingleStep = 0;
        Serial.println("WAIT");
        return;
      }

      if (str.startsWith("MOT,")) {
        if (motorsMoving) {
          Serial.println("BUSY");
          return;
        }
        motorErrorFlag = false;  // сброс флага ошибки для нового движения
        str = str.substring(4);
        for (byte i = 0; i < 5; i++) {
          targetPos[i] = str.substring(0, str.indexOf(",")).toInt();
          str = str.substring(str.indexOf(",") + 1);
          //if (i >= 2) motor[i].setMaxSpeed(2000);
          //if (i <= 1) motor[i].setMaxSpeed(2000);
          if (targetPos[i] > 999999) {
            Serial.println("ERROR");
            return;
          }
          if (i == 0 || i == 1) targetPos[i] *= 35.64;                  // перевод значений из шагов в мм
          if (i == 2 || i == 3) targetPos[i] *= 40.2;
          if (i == 4) targetPos[i] *= 25;
          round (targetPos[i]);
        }

        for (byte i = 0; i < 5; i++) {
          setEn(i, 0);
        }

        // Инициализация движения
        runMotFlags = 0;
        for (byte i = 0; i < 5; i++) {
          motor[i].moveTo(targetPos[i]);
          long d = motor[i].distanceToGo();
          if (d != 0) runMotFlags |= (1 << i);
          setDir(i, d > 0);
        }

        motorsMoving = true;
        Serial.println("WAIT");
        return;
      }

      if (str == "g") {                      //выдача всех ячеек
        str = "";
        for (byte i = 0; i < 114; i++) {                          // Выдача из 114 ячеек
          if (Serial.available()) {
            String cmd = Serial.readStringUntil('\n');
            cmd.trim();
            if (cmd == "$STOP") {
              Serial.println("Остановка по команде");
              break;  // выход из цикла for
            }
          }

          goo();
          count++;
          if (count > 113) count = 0;

          delay(10);
        }
      }
      if (str == "f") {                      //выдача 1 ячейки
        goo();
      }
      else Serial.println("UNKNOWN COMMAND");                   // Если неправильная команда
    }
  }
  if ((millis() - timer_lock0) > timer_lock && ind_l == HIGH) {             // Закрытие замка по таймеру
    shReg &= ~(1 << 2); setOuts();
    ind_l = LOW;
    timer_lock0 = 0;
    Serial.println("DONE");
  }
  if ((millis() - timer_sol_lock0) > timer_sol_lock && ind_s == HIGH) {     // Закрытие соленоида по таймеру
    shReg &= ~(1 << 4); setOuts();
    ind_s = LOW;
    timer_sol_lock0 = 0;
    Serial.println("DONE");
  }

  // Неблокирующее обновление
  if (zeroSingleActive) {
    zeroSingleUpdate();
  } else if (zeroActive) {
    zeroUpdate();
  } else if (motorsMoving) {
    motUpdate();
  } else {
    delay(5);
  }
}

void goo() {
  if (steps == 0) {

    if (count < 42) {
      shift = 15.2;                                 // было 15
      row = 0;
      shiftX = 0.5 * shift + shift * count;
    }
    else if (count < 69) {
      shift = 23.77;                                 // было 23
      row = 1;
      shiftX = 0.4 * shift + shift * (count - 42);  // было 0.5
    }
    else if (count < 87) {
      shift = 35.6;                                   // было 35
      row = 2;
      shiftX = 0.45 * shift + shift * (count - 69);  // было 0.5
    }
    else if (count < 102) {
      shift = 42.8;
      row = 3;
      shiftX = 0.45 * shift + shift * (count - 87);  // было 0.5
    }
    else if (count > 101) {
      shift = 53;
      row = 4;
      shiftX = 0.5 * shift + shift * (count - 102);
    }


    const byte thresholds1[] = {27, 59, 80, 96, 109};
    const byte thresholds2[] = {13, 50, 74, 91, 105};

    if (count > thresholds1[row]) shiftX += 6;
    if (count > thresholds2[row]) shiftX += 3;


    //for (byte i = 0; i < 5; i++) {
    //if ( i >= 2) motor[i].setMaxSpeed(2000);
    //if ( i <= 1) motor[i].setMaxSpeed(2000);
    //}

    pos[0] = cordZ[row] * 36;                               // позиция нужного ряда
    pos[1] = cordZ[row] * 36;
    pos[2] = 0;
    pos[3] = 0;
    pos[4] = 0;
    motRun();

    // max X2 = 47500 шагов
    // max X1 = 51000 шагов
    float cordX = 638 - shiftX;
    round (pos[2] = cordX * 40.2);                          // с округлением
    round (pos[3] = (cordX - 25) * 40.2);
    if (pos[3] < -50) pos[3] = -50;
    if (pos[3] > 23700) pos[3] = 23700;

    setEn(2, 0);                                          // Включение моторов
    setEn(3, 0);
    setEn(4, 0);
    if (motRun()) steps = 1;
  }

  if (steps == 1) {

    pos[4] = 1150;
    motor[4].setAcceleration(5000);
    //motor[4].setMaxSpeed(2000);
    if (motRun()) {
      pos[4] = 800;
      if (motRun()) {
        pos[4] = 1150;
        if (motRun()) {
          delay(800);
          motor[4].setAcceleration(3000);
          setDir(4, 0);
          motor[4].setCurrentPosition(0);
          motor[4].moveTo(-999999);
          while (~PINC & (1 << konc[4]))
            motor[4].run();
          setDir(4, 1);
          motor[4].setCurrentPosition(0);
          motor[4].moveTo(100);
          while (motor[4].run());
          motor[4].setCurrentPosition(0);
          steps = 2;
        }
      }
    }
    setEn(4, 1);
  }

  if (steps == 2) {

    for (byte i = 0; i < 2; i++) {          // Выставление в исходную позицию
      if (i == 0) {
        setDir(2, 0);
        setDir(3, 0);
        motor[2].setCurrentPosition(0);
        motor[3].setCurrentPosition(0);
        //motor[2].setMaxSpeed(2000);
        //motor[3].setMaxSpeed(2000);
        motor[2].moveTo(-999999);
        motor[3].moveTo(-999999);
        while ((~PINC & (1 << konc[2])) || (~PINC & (1 << konc[3]))) {
          if (~PINC & (1 << konc[2]))
            motor[2].run();
          if (~PINC & (1 << konc[3]))
            motor[3].run();
        }
        setDir(2, 1);
        setDir(3, 1);
        motor[2].setCurrentPosition(0);
        motor[3].setCurrentPosition(0);
        motor[2].moveTo(100);
        motor[3].moveTo(100);
        while ((PINC & (1 << konc[2])) || (PINC & (1 << konc[3]))) {
          if (PINC & (1 << konc[2]))
            motor[2].run();
          if (PINC & (1 << konc[3]))
            motor[3].run();
        }
        motor[2].setCurrentPosition(0);
        motor[3].setCurrentPosition(0);
        motor[2].moveTo(100);
        motor[3].moveTo(100);

        while (motor[2].distanceToGo() != 0 || motor[3].distanceToGo() != 0) {
          if (motor[2].distanceToGo() != 0 )
            motor[2].run();
          if (motor[3].distanceToGo() != 0 )
            motor[3].run();
        }
        motor[2].setCurrentPosition(0);
        motor[3].setCurrentPosition(0);
        setEn(2, 1);
        setEn(3, 1);
      } else if (i == 1) {
        setDir(0, 0);
        setDir(1, 0);
        //motor[0].setMaxSpeed(2000);
        //motor[1].setMaxSpeed(2000);
        motor[0].moveTo(0);
        motor[1].moveTo(0);
        while (motor[0].distanceToGo() != 0 || motor[1].distanceToGo() != 0) {
          if (motor[0].distanceToGo() != 0 )
            motor[0].run();
          if (motor[1].distanceToGo() != 0 )
            motor[1].run();
        }
        uint16_t tempSpeed = motor[0].maxSpeed();
        motor[0].setMaxSpeed(500);
        motor[1].setMaxSpeed(500);
        motor[0].moveTo(-9999);
        motor[1].moveTo(-9999);
        while ((~PINC & (1 << konc[0])) || (~PINC & (1 << konc[1]))) {
          if (~PINC & (1 << konc[0]))
            motor[0].run();
          if (~PINC & (1 << konc[1]))
            motor[1].run();
        }
        motor[0].setMaxSpeed(tempSpeed);
        motor[1].setMaxSpeed(tempSpeed);
        setDir(0, 1);
        setDir(1, 1);
        motor[0].setCurrentPosition(0);
        motor[1].setCurrentPosition(0);
        motor[0].moveTo(100);
        motor[1].moveTo(100);
        while ((PINC & (1 << konc[0])) || (PINC & (1 << konc[1]))) {
          if (PINC & (1 << konc[0]))
            motor[0].run();
          if (PINC & (1 << konc[1]))
            motor[1].run();
        }
        motor[0].setCurrentPosition(0);
        motor[1].setCurrentPosition(0);
        motor[0].moveTo(100);
        motor[1].moveTo(100);
        while (motor[0].distanceToGo() != 0 || motor[1].distanceToGo() != 0) {
          if (motor[0].distanceToGo() != 0 )
            motor[0].run();
          if (motor[1].distanceToGo() != 0 )
            motor[1].run();
        }
        motor[0].setCurrentPosition(0);
        motor[1].setCurrentPosition(0);
      }

    }
    steps = 0;
    Serial.print("выдана ячейка ");
    Serial.println(count + 1);
  }
}

bool motUpdate() {
  static bool errorFlag = false; // локальный статический флаг
  bool anyMoving = false;        // есть ли ещё движущиеся моторы

  for (byte i = 0; i < 5; i++) {
    if (runMotFlags & (1 << i)) {
      // Проверка концевика для этого мотора
      bool limitPressed = (PINC & (1 << konc[i]));
      if (limitPressed) {                               // если концевик нажат
        // Остановка мотора
        runMotFlags &= ~(1 << i);
        if (i >= 2) setEn(i, 1);
        Serial.print("ERROR MOTOR ");
        Serial.println(i + 1);
        motorErrorFlag = true;
        // Продолжаем проверять другие моторы (сломанный уже не двигается)
      } else {
        // Если концевик не нажат, обновляем мотор
        if (!motor[i].run()) {
          // Мотор доехал до цели
          runMotFlags &= ~(1 << i);
          // выключение моторов 3,4,5
          if (i >= 2) {
            if (i == 4 && motor[4].currentPosition() == 0)setEn(i, 1);
            else setEn(i, 1);
          }
        } else {
          anyMoving = true; // мотор ещё движется
        }
      }
    }
  }

  // Если ни один мотор не движется
  if (runMotFlags == 0) {
    motorsMoving = false;
    if (motorErrorFlag) {
      Serial.println("ERROR");
      motorErrorFlag = false; // сброс для следующего движения
    } else {
      Serial.println("DONE");
    }
    return false; // движение завершено
  }

  // Есть ещё движущиеся моторы
  return true;
}

void zeroUpdate() {
  if (!zeroActive) return;

  if (zeroStep == 0) {
    if (zeroMotorIdx == 0) zeroMotorIdx = 4;
    if (zeroMotorIdx >= 2) {
      byte i = zeroMotorIdx;
      switch (zeroSubStep) {
        case 0:
          setEn(i, 0);
          setDir(i, 0);
          motor[i].setCurrentPosition(0);
          motor[i].setMaxSpeed(1000);
          motor[i].moveTo(-999999);
          zeroSubStep = 1;
          break;
        case 1:
          if (~PINC & (1 << konc[i])) {
            motor[i].run();
          } else {
            // Концевик нажался – переход к отъезду
            setDir(i, 1);
            motor[i].setCurrentPosition(0);
            motor[i].moveTo(100);
            zeroSubStep = 2;
          }
          break;
        case 2: // Пока концевик не отпустил (PINC & (1<<konc[i]))
          if (PINC & (1 << konc[i])) {
            motor[i].run();
          } else {
            // Концевик отпущен – отъезд на 50
            motor[i].setCurrentPosition(0);
            motor[i].moveTo(50);
            zeroSubStep = 3;
          }
          break;
        case 3:
          if (motor[i].distanceToGo() != 0) {
            motor[i].run();
          } else {
            motor[i].setCurrentPosition(0);
            // Переход к следующему мотору
            zeroMotorIdx--;
            zeroSubStep = 0;
            if (zeroMotorIdx < 2) {
              // Все одиночные моторы обработаны – переход к паре (0,1)
              zeroStep = 1;
              zeroMotorIdx = 1;
              zeroSubStep = 0;
            }
          }
          break;
      }
      return; // выход, чтобы в следующем вызове продолжить
    }
  }

  //Обработка пары моторов 0 и 1 вместе
  if (zeroStep == 1) {
    switch (zeroSubStep) {
      case 0: // Инициализация пары
        setDir(0, 0);
        setDir(1, 0);
        motor[0].setCurrentPosition(0);
        motor[1].setCurrentPosition(0);
        motor[0].setMaxSpeed(1000);
        motor[1].setMaxSpeed(1000);
        motor[0].moveTo(-999999);
        motor[1].moveTo(-999999);
        zeroSubStep = 1;
        break;
      case 1: // Едут оба, пока хотя бы один концевик не нажат
        {
          bool leftNoPressed  = (~PINC & (1 << konc[0]));
          bool rightNoPressed = (~PINC & (1 << konc[1]));
          if (leftNoPressed || rightNoPressed) {
            if (leftNoPressed)  motor[0].run();
            if (rightNoPressed) motor[1].run();
          } else {
            // Оба концевика нажаты – смена направления
            setDir(0, 1);
            setDir(1, 1);
            motor[0].setCurrentPosition(0);
            motor[1].setCurrentPosition(0);
            motor[0].moveTo(100);
            motor[1].moveTo(100); 
            zeroSubStep = 2;
          }
        }
        break;
      case 2: // Ждём отпускания обоих концевиков
        {
          bool leftPressed  = (PINC & (1 << konc[0]));
          bool rightPressed = (PINC & (1 << konc[1]));
          if (leftPressed || rightPressed) {
            if (leftPressed)  motor[0].run();
            if (rightPressed) motor[1].run();
          } else {
            // Оба отпущены – ещё раз вперёд на 100
            motor[0].setCurrentPosition(0);
            motor[1].setCurrentPosition(0);
            motor[0].moveTo(50);
            motor[1].moveTo(50);                                                                                             //
            zeroSubStep = 3;
          }
        }
        break;
      case 3:
        {
          bool run0 = (motor[0].distanceToGo() != 0);
          bool run1 = (motor[1].distanceToGo() != 0);
          if (run0 || run1) {
            if (run0) motor[0].run();
            if (run1) motor[1].run();
            // Сброс позиции при случайном нажатии концевика
            if (PINC & (1 << konc[0])) motor[0].setCurrentPosition(0);
            if (PINC & (1 << konc[1])) motor[1].setCurrentPosition(0);
          } else {
            // Движение завершено
            motor[0].setCurrentPosition(0);
            motor[1].setCurrentPosition(0);
            zeroSubStep = 4;
          }
        }
        break;
      case 4:
        // Калибровка завершена
        zeroActive = false;
        // Выключение моторов X и Y
        for (byte i = 2; i < 5; i++) {
          setEn(i, 1);
        }
        Serial.println("DONE");
        break;
    }
    return;
  }
}

void zeroSingleUpdate() {
  if (!zeroSingleActive) return;

  byte i = zeroSingleMotor;
  if (i > 1) {
    switch (zeroSingleStep) {
      case 0: // Инициализация: включаем мотор, ставим направление к концевику, сбрасываем позицию, скорость, едем назад
        setEn(i, 0);                     // включить драйвер
        setDir(i, 0);                    // направление к концевику (0 = назад)
        motor[i].setCurrentPosition(0);
        motor[i].setMaxSpeed(1500);
        motor[i].moveTo(-999999);
        zeroSingleStep = 1;
        break;

      case 1: // Ждём, пока концевик не нажмётся
        if (~PINC & (1 << konc[i])) {    // концевик ещё не нажат
          motor[i].run();
        } else {
          // Концевик нажат – останавливаем движение, меняем направление, отъезжаем на 200
          setDir(i, 1);
          motor[i].setCurrentPosition(0);
          motor[i].moveTo(200);
          zeroSingleStep = 2;
        }
        break;

      case 2: // Ждём, пока концевик отпустится
        if (PINC & (1 << konc[i])) {     // концевик всё ещё нажат
          motor[i].run();
        } else {
          // Концевик отпущен – отъезжаем на 100
          motor[i].setCurrentPosition(0);
          motor[i].moveTo(100);
          zeroSingleStep = 3;
        }
        break;

      case 3: // Ждём завершения движения (distanceToGo == 0)
        if (motor[i].distanceToGo() != 0) {
          motor[i].run();
        } else {
          motor[i].setCurrentPosition(0);
          // Калибровка завершена
          zeroSingleActive = false;

          setEn(i, 1);
          Serial.println("DONE");
        }
        break;
    }
  }
  if (i == 0 || i == 1) {
    switch (zeroSingleStep) {
      case 0: // Инициализация пары
        setDir(0, 0);
        setDir(1, 0);
        motor[0].setCurrentPosition(0);
        motor[1].setCurrentPosition(0);
        motor[0].setMaxSpeed(1000);
        motor[1].setMaxSpeed(1000);
        motor[0].moveTo(-999999);
        motor[1].moveTo(-999999);
        zeroSingleStep = 1;
        break;
      case 1: // Едут оба, пока хотя бы один концевик не нажат
        {
          bool leftNoPressed  = (~PINC & (1 << konc[0]));
          bool rightNoPressed = (~PINC & (1 << konc[1]));
          if (leftNoPressed || rightNoPressed) {
            if (leftNoPressed)  motor[0].run();
            if (rightNoPressed) motor[1].run();
          } else {
            // Оба концевика нажаты – смена направления
            setDir(0, 1);
            setDir(1, 1);
            motor[0].setCurrentPosition(0);
            motor[1].setCurrentPosition(0);
            motor[0].moveTo(100);
            motor[1].moveTo(100);
            zeroSingleStep = 2;
          }
        }
        break;
      case 2: // Ждём отпускания обоих концевиков
        {
          bool leftPressed  = (PINC & (1 << konc[0]));
          bool rightPressed = (PINC & (1 << konc[1]));
          if (leftPressed || rightPressed) {
            if (leftPressed)  motor[0].run();
            if (rightPressed) motor[1].run();
          } else {
            // Оба отпущены – ещё раз вперёд на 100
            motor[0].setCurrentPosition(0);
            motor[1].setCurrentPosition(0);
            motor[0].moveTo(100);
            motor[1].moveTo(100);
            zeroSingleStep = 3;
          }
        }
        break;
      case 3:
        {
          bool run0 = (motor[0].distanceToGo() != 0);
          bool run1 = (motor[1].distanceToGo() != 0);
          if (run0 || run1) {
            if (run0) motor[0].run();
            if (run1) motor[1].run();
            // Сброс позиции при случайном нажатии концевика
            if (PINC & (1 << konc[0])) motor[0].setCurrentPosition(0);
            if (PINC & (1 << konc[1])) motor[1].setCurrentPosition(0);
          } else {
            // Движение завершено
            motor[0].setCurrentPosition(0);
            motor[1].setCurrentPosition(0);
            zeroSingleStep = 4;
          }
        }
        break;
      case 4:
        // Калибровка завершена
        zeroSingleActive = false;
        // Выключение моторов X и Y
        for (byte i = 2; i < 5; i++) {
          setEn(i, 1);
        }
        Serial.println("DONE");
        break;
    }
  }
}

bool motRun() {
  byte runMot = 0;                          // Сброс флагов
  for (byte i = 0; i < 5; i++) {
    motor[i].moveTo(pos[i]);                // Позиция
    long d = motor[i].distanceToGo();       // Направление вращения и дистанция
    if (d != 0) runMot |= (1 << i);         // Флаг вращения для ускорения опроса
    setDir(i, d > 0);                       // Направление вращения
    //setEn(n, 0);                            // Включение драйвера
  }
  while (runMot) {                          // Пока надо крутить моторы
    if (PINC & 0b111011) return false;      // Если сработал концевик любого из 5 моторов
    for (byte i = 0; i < 5; i++)
      if (runMot & (1 << i))                // Если мотор надо крутить
        if (!motor[i].run())                // Если мотор доехал
          runMot &= ~(1 << i);              // Сброс флага
  } return true;
}




void setEn(byte n, bool st) {
  if (st) {
    if (n == 0) shReg |= (1 << 9);
    if (n == 1) shReg |= (1 << 11);
    if (n == 2) shReg |= (1 << 13);
    if (n == 3) shReg |= (1 << 1);
    if (n == 4) shReg |= (1 << 14);
  } else {
    if (n == 0) shReg &= ~(1 << 9);
    if (n == 1) shReg &= ~(1 << 11);
    if (n == 2) shReg &= ~(1 << 13);
    if (n == 3) shReg &= ~(1 << 1);
    if (n == 4) shReg &= ~(1 << 14);
  } setOuts();
}

void setDir(byte n, bool st) {
  if (inv[n]) st = !st;
  if (st) {
    if (n == 0) shReg |= (1 << 8);
    if (n == 1) shReg |= (1 << 10);
    if (n == 2) shReg |= (1 << 12);
    if (n == 3) shReg |= (1 << 0);
    if (n == 4) shReg |= (1 << 15);
  } else {
    if (n == 0) shReg &= ~(1 << 8);
    if (n == 1) shReg &= ~(1 << 10);
    if (n == 2) shReg &= ~(1 << 12);
    if (n == 3) shReg &= ~(1 << 0);
    if (n == 4) shReg &= ~(1 << 15);
  } setOuts();
}


void setOuts() {
  digitalWrite(8, LOW);
  for (byte i = 0; i < 16; i++) {
    digitalWrite(7, (shReg >> (15 - i)) & 1);
    digitalWrite(9, HIGH);
    digitalWrite(9, LOW);
  }
  digitalWrite(8, HIGH);
}
