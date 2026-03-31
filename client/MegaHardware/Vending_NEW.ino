
/*
     КОМАНДЫ
  $LOCK         Открыть замки на 10 сек. Ответ OK
  $LOCK0        Открыть замки. Ответ LOCK OFF
  $LOCK1        Закрыть замки. Ответ LOCK ON
  $ZERO         Отправить все моторы в нулевое положение. Доедут до концевиков и в исходное положение. Ответ ОК, после завершения DONE
  $LED,x        Задать яркость ленты x(0-255). Ответ OK
  $MOT1,x       Отправить мотор 1 (XP4) в позицию x(0-9999). Ответ ОК, после завершения DONE
  $MOT2,x       Отправить мотор 2 (XP6) в позицию x(0-9999). Ответ ОК, после завершения DONE
  $MOT3,x       Отправить мотор 3 (XP8) в позицию x(0-9999). Ответ ОК, после завершения DONE
  $MOT4,x       Отправить мотор 4 (XP10) в позицию x(0-9999). Ответ ОК, после завершения DONE
  

*/
#include <AccelStepper.h> // https://downloads.arduino.cc/libraries/github.com/waspinator/AccelStepper-1.64.0.zip
#include <FastLED.h>      // 



// Шаговик 1
#define PUL1 A4 // XP4
#define DIR1 A5
#define ENA1 2

// Шаговик 2
#define PUL2 9  // XP6
#define DIR2 8
#define ENA2 7

// Шаговик 3
#define PUL3 3  // XP8
#define DIR3 4
#define ENA3 10

// Шаговик 4
#define PUL4 6  // XP10
#define DIR4 12
#define ENA4 13

// Шаговик 5                                   ИЗМЕНИТЬ ПИНЫ
#define PUL5 5  // XP12
#define DIR5 11
#define ENA5 22

// Концевики
#define KONC1 A3  // XP5
#define KONC2 A2  // XP7
#define KONC3 A1  // XP9
#define KONC4 A0  // XP11

#define LED 5   // Светодиодная лента
#define LOCK 11 // Замок

//  #define NUM_LEDS 5      // Адресная лента, количество светодиодов
//  #define A_LED 23        // Пин подключения ленты                                     ИЗМЕНИТЬ ПИНЫ
//  CRGB leds[NUM_LEDS];

AccelStepper motor[] = {
  AccelStepper(1, PUL1, DIR1),
  AccelStepper(1, PUL2, DIR2),
  AccelStepper(1, PUL3, DIR3),
  AccelStepper(1, PUL4, DIR4),
  AccelStepper(1, PUL5, DIR5)
};

byte konc[] = {KONC1, KONC2, KONC3, KONC4};

uint32_t timer_lock;                                    // Таймер замка

uint16_t speed1, speed2, speed3, speed4, speed5;   // значения до 65 535
uint16_t boost1, boost2, boost3, boost4, boost5;   // значения до 65 535

void setup() {
  Serial.begin(9600);
  pinMode(LOCK, OUTPUT);
  pinMode(LED, OUTPUT);

  for (byte i = 0; i < 4; i++)
    motor[i].setAcceleration(1000);

 // FastLED.addLeds <WS2812, A_LED, GRB>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);       // настройки адресной ленты
 // FastLED.setBrightness(255);                                                                // яркость адресной ленты
}

void lock() { // Открытие замка
  digitalWrite(LOCK, HIGH);
  delay(timer_lock);
  digitalWrite(LOCK, LOW);
}

void lock_H() { // Открытие замка
  digitalWrite(LOCK, HIGH);
}

void lock_L() { // закрытие замка
  digitalWrite(LOCK, LOW);
}

void zero() {
  for (byte i = 0; i < 4; i++) {
    motor[i].setMaxSpeed(500);
    motor[i].setCurrentPosition(0);
    motor[i].moveTo(-999999999);
    while (motor[i].run())
      if (digitalRead(konc[i])) {
        motor[i].setCurrentPosition(0);
        break;
      }
  }
}

bool motRun(byte n) {
  //motor[n].moveTo(n);
  while (motor[n].run());
  //if (digitalRead(konc[n])) {
  //  motor[n].setCurrentPosition(0);
  //  return false;
  //}
  return true;
}

void sensVal(byte s) {
  if (digitalRead(konc[s])) {
    Serial.print("SENS"); Serial.print(s = s + 1); Serial.println("_1");
  } else {
    Serial.print("SENS");
    Serial.print(s = s + 1);
    Serial.println("_0");
  }
}

void loop() {
  while (!Serial.available()) delay(10);
  if (Serial.read() != '$') return;

  String str = Serial.readStringUntil('\n');



  if (str == "LOCK0") {                                       // Если команда открытия замка
    Serial.println("LOCK OFF"); lock_H();
  }
  if (str == "LOCK1") {                                       // Если команда закрытия замка
    Serial.println("LOCK ON"); lock_L();
  }
  if (str.startsWith("LOCK,")) {                              // Если команда открытия замка
    uint32_t timer_l = str.substring(5).toInt();              // Получение подстроки начиная с запятой и преобразование в int
    timer_lock = timer_l;
    Serial.println("OK"); lock();
  }
  if (str == "ZERO") {                                        // Если команда установить моторы в начальное положение
    Serial.println("OK"); zero(); Serial.println("DONE");
  }



 /* if (str.startsWith("A_LED,")) {
    uint8_t R = str.substring(6, 9).toInt();
    uint8_t G = str.substring(10, 13).toInt();
    uint8_t B = str.substring(14, 17).toInt();
    for (byte i = 0; i < NUM_LEDS; i++) {
      leds[i] = CHSV(R, G, B);
    }
  }*/



  if (str == "SENS1") {                            // Если команда опроса датчика 1
    Serial.println("OK"); sensVal(0);
  }
  if (str == "SENS2") {                            // Если команда опроса датчика 2
    Serial.println("OK"); sensVal(1);
  }
  if (str == "SENS3") {                            // Если команда опроса датчика 3
    Serial.println("OK"); sensVal(2);
  }
  if (str == "SENS4") {                            // Если команда опроса датчика 4
    Serial.println("OK"); sensVal(3);
  }



  if (str.startsWith("LED,")) {                    // Если команда яркости ленты
    uint16_t pwm = str.substring(4).toInt();       // Получение подстроки начиная с запятой и преобразование в int
    if (-1 < pwm && pwm < 256) {                   // Если значение ШИМ считано верно
      Serial.println("OK");                        // Ответ малине
      analogWrite(LED, pwm);                       // Подача ШИМ
    } else Serial.println("ERROR");                // Если значение с ошибкой
  }



  if (str.startsWith("MOT1_SPEED,")) {             // Если команда настройки скорости мотора 1
    uint16_t sp = str.substring(11).toInt();       // Получение подстроки начиная с запятой и преобразование в int
    speed1 = sp;
    Serial.println("OK");                          // Ответ малине
  }
  if (str.startsWith("MOT1_BOOST,")) {             // Если команда настройки ускорения мотора 1
    uint16_t boost = str.substring(11).toInt();    // Получение подстроки начиная с запятой и преобразование в int
    boost1 = boost;
    Serial.println("OK");                          // Ответ малине
  }

  if (str.startsWith("MOT2_SPEED,")) {             // Если команда настройки скорости мотора 2
    uint16_t sp = str.substring(11).toInt();       // Получение подстроки начиная с запятой и преобразование в int
    speed2 = sp;
    Serial.println("OK");                          // Ответ малине
  }
  if (str.startsWith("MOT2_BOOST,")) {             // Если команда настройки ускорения мотора 2
    uint16_t boost = str.substring(11).toInt();    // Получение подстроки начиная с запятой и преобразование в int
    boost2 = boost;
    Serial.println("OK");                          // Ответ малине
  }

  if (str.startsWith("MOT3_SPEED,")) {             // Если команда настройки скорости мотора 3
    uint16_t sp = str.substring(11).toInt();       // Получение подстроки начиная с запятой и преобразование в int
    speed3 = sp;
    Serial.println("OK");                          // Ответ малине
  }
  if (str.startsWith("MOT3_BOOST,")) {             // Если команда настройки ускорения мотора 3
    uint16_t boost = str.substring(11).toInt();    // Получение подстроки начиная с запятой и преобразование в int
    boost3 = boost;
    Serial.println("OK");                          // Ответ малине
  }

  if (str.startsWith("MOT4_SPEED,")) {             // Если команда настройки скорости мотора 4
    uint16_t sp = str.substring(11).toInt();       // Получение подстроки начиная с запятой и преобразование в int
    speed4 = sp;
    Serial.println("OK");                          // Ответ малине
  }
  if (str.startsWith("MOT4_BOOST,")) {             // Если команда настройки ускорения мотора 4
    uint16_t boost = str.substring(11).toInt();    // Получение подстроки начиная с запятой и преобразование в int
    boost4 = boost;
    Serial.println("OK");                          // Ответ малине
  }

  if (str.startsWith("MOT5_SPEED,")) {             // Если команда настройки скорости мотора 5
    uint16_t sp = str.substring(11).toInt();       // Получение подстроки начиная с запятой и преобразование в int
    speed5 = sp;
    Serial.println("OK");                          // Ответ малине
  }
  if (str.startsWith("MOT5_BOOST,")) {             // Если команда настройки ускорения мотора 5
    uint16_t boost = str.substring(11).toInt();    // Получение подстроки начиная с запятой и преобразование в int
    boost5 = boost;
    Serial.println("OK");                          // Ответ малине
  }



  if (str.startsWith("MOT1,")) {                 // Если команда мотора 1 (XP4)
    uint16_t pos = str.substring(5).toInt();     // Получение подстроки начиная с запятой и преобразование в int
    pos = pos * 71.1;
    if (pos < 31995) {                           // Если значение позиции в диапазоне 0-450 мм
      Serial.println("OK");                      // Ответ малине
      motor[0].setMaxSpeed(speed1);              // Макс. скорость шагов/сек
      motor[0].setAcceleration(boost1);          // Ускорение шагов/сек^2
      motor[0].moveTo(pos);                      // Движение на pos шагов
      if (motRun(0)) Serial.println("DONE");
      else Serial.println("ERROR");              // Если мотор упёрся в свой концевик
    }
  }

  if (str.startsWith("MOT2,")) {                 // Если команда мотора 2 (XP6)
    uint16_t pos = str.substring(5).toInt();     // Получение подстроки начиная с запятой и преобразование в int
    pos = pos * 80;
    if (pos < 46800) {                           // Если значение позиции в диапазоне 0-585 мм
      Serial.println("OK");                      // Ответ малине
      motor[1].setMaxSpeed(speed2);              // Макс. скорость шагов/сек
      motor[1].setAcceleration(boost2);             // Ускорение шагов/сек^2
      motor[1].moveTo(pos);                      // Движение на pos шагов
      if (motRun(1)) Serial.println("DONE");
      else Serial.println("ERROR");              // Если мотор упёрся в свой концевик
    }
  }

  if (str.startsWith("MOT3,")) {                 // Если команда мотора 3 (XP8)
    uint16_t pos = str.substring(5).toInt();     // Получение подстроки начиная с запятой и преобразование в int
    pos = pos * 80;
    if (pos < 49600) {                           // Если значение позиции в диапазоне 0-620 мм
      Serial.println("OK");                      // Ответ малине
      motor[2].setMaxSpeed(speed3);              // Макс. скорость шагов/сек
      motor[2].setAcceleration(boost3);          // Ускорение шагов/сек^2
      motor[2].moveTo(pos);                      // Движение на pos шагов
      if (motRun(2)) Serial.println("DONE");
      else Serial.println("ERROR");              // Если мотор упёрся в свой концевик
    }
  }

  if (str.startsWith("MOT4,")) {                 // Если команда мотора 4 (XP10)
    uint16_t pos = str.substring(5).toInt();     // Получение подстроки начиная с запятой и преобразование в int
    pos = pos * 103;
    if (pos < 5665) {                            // Если значение позиции в диапазоне 0-55 мм
      Serial.println("OK");                      // Ответ малине
      motor[3].setMaxSpeed(speed4);              // Макс. скорость шагов/сек
      motor[3].setAcceleration(boost4);          // Ускорение шагов/сек^2
      motor[3].moveTo(pos);                      // Движение на pos шагов
      if (motRun(3)) Serial.println("DONE");
      else Serial.println("ERROR");              // Если мотор упёрся в свой концевик
    }
  }

  if (str.startsWith("MOT5,")) {                 // Если команда мотора 5 (XP12)
    uint16_t pos = str.substring(5).toInt();     // Получение подстроки начиная с запятой и преобразование в int
    if (pos < 9999) {                            // Если значение позиции в диапазоне 0-9999
      Serial.println("OK");                      // Ответ малине
      motor[4].setMaxSpeed(speed5);              // Макс. скорость шагов/сек
      motor[4].setAcceleration(boost5);          // Ускорение шагов/сек^2
      motor[4].moveTo(pos);                      // Движение на pos шагов
      if (motRun(4)) Serial.println("DONE");
      else Serial.println("ERROR");              // Если мотор упёрся в свой концевик
    }
  }
  for (byte i = 0; i < 4; i++) {
    motor[i].run();
  }
}
