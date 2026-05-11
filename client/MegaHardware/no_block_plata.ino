


#include <AccelStepper.h> // https://downloads.arduino.cc/libraries/github.com/waspinator/AccelStepper-1.64.0.zip
#include <microLED.h>     // https://github.com/GyverLibs/microLED/archive/refs/heads/main.zip


microLED<30, 10, MLED_NO_CLOCK, LED_WS2818, ORDER_GRB, CLI_AVER> strip;  // Количество светодиодов, ножка
const byte konc[] = {3, 4, 5, 0, 1, 2}; // Номера портов PC у концевиков 0-5
//const byte konc[] = {5, 1, 0, 3, 4, 2}; // Номера портов PC у концевиков 0-5
long pos[5];                            // Позиции моторов
const byte inv[] = {0, 0, 0, 0, 0};     // Инвертирование направления моторов 1-5. Если 1, то инвертирован
AccelStepper motor[] = {
  AccelStepper(1, 2, 12),
  AccelStepper(1, 3, 12),
  AccelStepper(1, 4, 12),
  AccelStepper(1, 5, 12),
  AccelStepper(1, 6, 12)
};


uint16_t shReg; // Состояние регистра

int16_t cordZ[] = {416, 328, 229, 119, 0};  // корды рядов
float shift;
uint16_t row, count;
float shiftX;
bool go, zapret;
uint8_t steps;

void setup() {
  Serial.begin(9600);
  pinMode(9, OUTPUT); //CLK
  pinMode(7, OUTPUT); // DATA
  pinMode(8, OUTPUT); // LATCH
  setOuts();

  for (byte i = 0; i < 5; i++)
    motor[i].setAcceleration(5000);

  strip.clear();
  strip.setBrightness(100);
  strip.set(0, mRGB(255, 255, 255));
  strip.show();
}

//$RGB,180,255,30 Задать цвет адресной ленте
//$LOCK открыть замок
//$LED,1 включить ленту 1, выключить 0
//$SOL дёрнуть соленоид
//$ZERO Все моторы в ноль
//$MOT,0,0,0,0,0 Моторы 1-5 в позиции через запятую. Если не надо двигать, то надо отправить старую позицию
//$MOT,1000,1000,1000,1000,1000
//$g запустить выдачу всех ячеек подряд
//$c, задать номер выдаваемой ячейки
//$f выдать одну ячейку

void loop() {
  while (!Serial.available()) delay(10);
  if (Serial.read() != '$') return;
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
    uint16_t st = str.substring(5).toInt();     // Получение подстроки начиная с запятой и преобразование в int
    shReg |= (1 << 2); setOuts();
    delay(st);
    shReg &= ~(1 << 2); setOuts();
    Serial.println("DONE");
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
    uint16_t st = str.substring(4).toInt();     // Получение подстроки начиная с запятой и преобразование в int
    shReg |= (1 << 4); setOuts();
    delay(st);
    shReg &= ~(1 << 4); setOuts();
    Serial.println("DONE");
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

  if (str == "ZERO") {                      // Если команда установить моторы в начальное положение
    Serial.println("WAIT");

    for (byte i = 4; i > 0; i--) {          // Выставление в исходную позицию
      if (i == 1) {
        setDir(0, 0);
        setDir(1, 0);
        motor[0].setCurrentPosition(0);
        motor[1].setCurrentPosition(0);
        motor[0].setMaxSpeed(1500);
        motor[1].setMaxSpeed(1500);
        motor[0].moveTo(-999999);
        motor[1].moveTo(-999999);
        while ((~PINC & (1 << konc[0])) || (~PINC & (1 << konc[1]))) {
          if (~PINC & (1 << konc[0]))
            motor[0].run();
          if (~PINC & (1 << konc[1]))
            motor[1].run();
        }
        setDir(0, 1);
        setDir(1, 1);
        motor[0].setCurrentPosition(0);
        motor[1].setCurrentPosition(0);
        motor[0].moveTo(200);
        motor[1].moveTo(200);
        while ((PINC & (1 << konc[0])) || (PINC & (1 << konc[1]))) {
          if (PINC & (1 << konc[0]))
            motor[0].run();
          if (PINC & (1 << konc[1]))
            motor[1].run();
        }
        motor[0].setCurrentPosition(0);
        motor[1].setCurrentPosition(0);
        motor[0].moveTo(200);
        motor[1].moveTo(200);
        while (motor[0].distanceToGo() != 0 || motor[1].distanceToGo() != 0) {
          if (motor[0].distanceToGo() != 0 )
            motor[0].run();
          if (motor[1].distanceToGo() != 0 )
            motor[1].run();
          if (PINC & (1 << konc[0]))
            motor[0].setCurrentPosition(0);
          if (PINC & (1 << konc[1]))
            motor[1].setCurrentPosition(0);
        }
        motor[0].setCurrentPosition(0);
        motor[1].setCurrentPosition(0);
      } else {
        setEn(i, 0);
        setDir(i, 0);
        motor[i].setCurrentPosition(0);
        motor[i].setMaxSpeed(1500);
        motor[i].moveTo(-999999);
        while (~PINC & (1 << konc[i]))
          motor[i].run();
        setDir(i, 1);
        motor[i].setCurrentPosition(0);
        motor[i].moveTo(200);
        while (PINC & (1 << konc[i])) {
          if (PINC & (1 << konc[i]))
            motor[i].run();
        }
        motor[i].setCurrentPosition(0);
        motor[i].moveTo(200);
        while (motor[i].run());
        motor[i].setCurrentPosition(0);
      }
    }
    for (byte i = 2; i < 5 ; i++) {
      if (motor[i].currentPosition() == 0) setEn(i, 1);     // Выключение X и Y моторов
    }
    Serial.println("DONE");
    return;
  }

  if (str.startsWith("MOT,")) {                             // Если команда движения моторов
    str = str.substring(4);
    for (byte i = 0; i < 5; i++) {
      pos[i] = str.substring(0, str.indexOf(",")).toInt();  // Запись новых позиций
      str = str.substring(str.indexOf(",") + 1);
      motor[i].setMaxSpeed(2000);
      if (pos[i] > 999999) {
        Serial.println("ERROR"); return;
      }
    } Serial.println("WAIT");                               // Ответ малине, чтобы ждала выполнения
    for (byte i = 0; i < 5 ; i++) {
      setEn(i, 0);                                          // Включение моторов
    }
    if (motRun()) Serial.println("DONE");                   // Если моторы доехали
    else Serial.println("ERROR");                           // Если мотор упёрся в свой концевик
    for (byte i = 2; i < 5 ; i++) {
      if (motor[i].currentPosition() == 0) setEn(i, 1);     // Выключение X и Y моторов
    }
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


    for (byte i = 0; i < 5; i++) {
      motor[i].setMaxSpeed(2000);
    }

    pos[0] = cordZ[row] * 72;                               // позиция нужного ряда
    pos[1] = cordZ[row] * 72;
    pos[2] = 0;
    pos[3] = 0;
    pos[4] = 0;
    motRun();

    // max X2 = 47500 шагов
    // max X1 = 51000 шагов
    float cordX = 638 - shiftX;
    round (pos[2] = cordX * 80.4);                          // с округлением
    round (pos[3] = cordX * 75);

    setEn(2, 0);                                          // Включение моторов
    setEn(3, 0);
    if (motRun()) steps = 1;
  }

  if (steps == 1) {
    setEn(4, 0);
    pos[4] = 4500;
    motor[4].setMaxSpeed(4000);
    if (motRun()) {
      setDir(4, 0);
      motor[4].setCurrentPosition(0);
      motor[4].moveTo(-999999);
      while (~PINC & (1 << konc[4]))
        motor[4].run();
      setDir(4, 1);
      motor[4].setCurrentPosition(0);
      motor[4].moveTo(200);
      while (motor[4].run());
      motor[4].setCurrentPosition(0);
      steps = 2;
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
        motor[2].setMaxSpeed(2000);
        motor[3].setMaxSpeed(2000);
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
        motor[2].moveTo(200);
        motor[3].moveTo(200);
        while ((PINC & (1 << konc[2])) || (PINC & (1 << konc[3]))) {
          if (PINC & (1 << konc[2]))
            motor[2].run();
          if (PINC & (1 << konc[3]))
            motor[3].run();
        }
        motor[2].setCurrentPosition(0);
        motor[3].setCurrentPosition(0);
        motor[2].moveTo(200);
        motor[3].moveTo(200);

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
        motor[0].setCurrentPosition(0);
        motor[1].setCurrentPosition(0);
        motor[0].setMaxSpeed(2000);
        motor[1].setMaxSpeed(2000);
        motor[0].moveTo(-999999);
        motor[1].moveTo(-999999);
        while ((~PINC & (1 << konc[0])) || (~PINC & (1 << konc[1]))) {
          if (~PINC & (1 << konc[0]))
            motor[0].run();
          if (~PINC & (1 << konc[1]))
            motor[1].run();
        }
        setDir(0, 1);
        setDir(1, 1);
        motor[0].setCurrentPosition(0);
        motor[1].setCurrentPosition(0);
        motor[0].moveTo(200);
        motor[1].moveTo(200);
        while ((PINC & (1 << konc[0])) || (PINC & (1 << konc[1]))) {
          if (PINC & (1 << konc[0]))
            motor[0].run();
          if (PINC & (1 << konc[1]))
            motor[1].run();
        }
        motor[0].setCurrentPosition(0);
        motor[1].setCurrentPosition(0);
        motor[0].moveTo(200);
        motor[1].moveTo(200);
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
