





#define SELMODE 12  // Контакт для входа в режим отладки. Для режима отладки соединить с GND перед включением

// Подключение экрана
#define SDA 20
#define SCL 21

// Подключение энкодеров
#define DTX A0  // Энкодер X
#define CLKX A1
#define DTY A2  // Энкодер Y
#define CLKY A3
#define DTZ A4  // Энкодер Z
#define CLKZ A5
#define BTN A6  // Подключение кнопки для пуска моторов при отладке


// Подключение драйверов
#define DIRX 23  // Драйвер X
#define PULX 25
#define DIRY 27  // Драйвер Y
#define PULY 29

// Концевики
#define KONCX 53
#define KONCY 51



// Количество шагов на один щелчок энкодера для каждой оси при отладке
#define DX 50
#define DY 50

// Максимальные координаты по осям
#define MAXX 4300
#define MAXY 3220
#define MAXZ 180

// Координаты, куда вернётся каретка после изъятия сверла
#define CX 2000
#define CY 1000

#define MULT 4        // Микрошаг
#define CALSP 1000    // Скорость моторов при отладке
#define WORKSP 4000   // Скорость моторов в обычном режиме

// Список точек, в которые могут пойти моторы.
uint16_t NUM = 512;  // Количество точек в памяти

#include <Wire.h>
#include <Servo.h>
#include "COORD.h"
#include <EncButton.h>          // https://github.com/GyverLibs/EncButton/archive/refs/heads/main.zip
#include <AccelStepper.h>       // https://downloads.arduino.cc/libraries/github.com/waspinator/AccelStepper-1.64.0.zip
#include <LiquidCrystal_I2C.h>  // https://downloads.arduino.cc/libraries/github.com/marcoschwartz/LiquidCrystal_I2C-1.1.2.zip
//Возможно придётся добавить GyverIO https://github.com/GyverLibs/GyverIO?ysclid=lrbvwa7mlm354384448

LiquidCrystal_I2C lcd(0x27, 16, 2);
AccelStepper stX(1, PULX, DIRX);
AccelStepper stY(1, PULY, DIRY);
EncButton ebX(DTX, CLKX);
EncButton ebY(DTY, CLKY);
EncButton ebZ(DTZ, CLKZ);
Servo myservo;

long pos[3];
uint16_t targ;  // Ячейка к которой надо ехать

void toggleBit(int pin) {
  int currentState = digitalRead(pin);
  digitalWrite(pin, !currentState);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(9600);
  Serial.print("\r\n");
  Serial.print("Инициализация");
  Serial1.begin(9600);
  pinMode(SELMODE, INPUT_PULLUP);
  pinMode(KONCX, INPUT_PULLUP);
  pinMode(KONCY, INPUT_PULLUP);
  pinMode(BTN, INPUT_PULLUP);
  Serial.print(".");
  stX.setAcceleration(10000);
  stY.setAcceleration(10000);
  stX.setMaxSpeed(WORKSP);
  stY.setMaxSpeed(WORKSP);
  Serial.print(".");
  myservo.attach(4);
  myservo.write(180);
  Serial.print(".");
  lcd.init();
  lcd.backlight();
  Serial.print(".");
  if (!digitalRead(SELMODE)) settingMode(); // Если режим настройки
  Serial.print(".");
  setZero();
  stX.moveTo(long(CX) * MULT);
  stY.moveTo(long(CY) * MULT);
  while (stX.run() || stY.run());
  
  lcd.setCursor(0, 0);
  lcd.print("Enter pos: ");
  Serial.print("\r\n");
  Serial.print("Устройство готово к работе");
  Serial.print("\r\n");
}

void loop() {
  while (Serial1.available() < 4) delay(10);
  if (Serial1.read() != '$') return;
  toggleBit(LED_BUILTIN);

  delay(10);

  targ = 0;
  uint16_t buf = Serial1.read();
  while (Serial1.available()) {
    buf = (buf << 8) | Serial1.read();
    if (buf == 0x0D0A){
      if (targ && targ <= NUM) {
        pos[0] = pgm_read_word(&Xmass[targ - 1]);
        pos[1] = pgm_read_word(&Ymass[targ - 1]);
        pos[2] = pgm_read_word(&Zmass[targ - 1]);
        Serial1.print("$1\n");
        Serial.print("Команда: ");
        Serial.println(targ);
        runToPos();
      }
    }
    else toggleBit(LED_BUILTIN);
    targ *= 10;
    targ += (buf >> 8) - 48;
  }
}

void runToPos() {
  stX.moveTo(pos[0] * MULT);
  stY.moveTo(pos[1] * MULT);
  while (stX.run() || stY.run());

  delay(300);
  myservo.write(pos[2]);
  delay(300);
  myservo.write(180);
  delay(300);
  Serial1.print("$2\n");
  //Serial.print("\r\n");
  Serial.print("Исполнено.");
  Serial.print("\r\n");

  stX.moveTo(long(CX) * MULT);
  stY.moveTo(long(CY) * MULT);
  while (stX.run() || stY.run());
}

void setZero() {
  Serial.print("\r\n");
  Serial.print("Начали установку нуля");
  bool bX, bY;
  stX.setMaxSpeed(CALSP);
  stY.setMaxSpeed(CALSP);
  stX.moveTo(-9999999);
  stY.moveTo(-9999999);
  Serial.print(".");

  do {
    if (bX) stX.run();
    if (bY) stY.run();
    delay(1);
    bX = digitalRead(KONCX);
    bY = digitalRead(KONCY);
  } while (bX || bY);
  Serial.print(".");
  stX.setCurrentPosition(0);
  stY.setCurrentPosition(0);
  Serial.print(".");
  stX.setMaxSpeed(WORKSP);
  stY.setMaxSpeed(WORKSP);
  Serial.print("Ок");
}

void updScreen(byte n) {
  lcd.setCursor(2, n);
  lcd.print(" ");
  if (pos[n] < 1000) lcd.print(" ");
  if (pos[n] < 100) lcd.print(" ");
  if (pos[n] < 10) lcd.print(" ");
  lcd.print(pos[n]);
}


void settingMode() {  // Режим отладки
  Serial.print("\r\n");
  Serial.print("Включён режим отладки");
  lcd.setCursor(0, 0);
  lcd.print("X ");
  lcd.setCursor(0, 1);
  lcd.print("Y ");
  lcd.setCursor(0, 2);
  lcd.print("Z ");
  updScreen(0);
  updScreen(1);
  updScreen(2);
  Serial.print(".");
  setZero();
  Serial.print(".");
  while (true) {
    if (Serial1.available()) {
      int p = Serial1.parseInt();
      Serial1.println(p);
      if (p && p <= NUM) {
        pos[0] = pgm_read_word(&Xmass[p - 1]);
        pos[1] = pgm_read_word(&Ymass[p - 1]);
        pos[2] = pgm_read_word(&Zmass[p - 1]);
        updScreen(0);
        updScreen(1);
        runToPos();
      }
    }
    Serial.print(".");
    ebX.tick();
    ebY.tick();
    ebZ.tick();
    Serial.print(".");
    if (ebX.left() && pos[0]) {
      pos[0] -= DX;
      updScreen(0);
    }
    Serial.print(".");    
    if (ebX.right() && pos[0] < MAXX) {
      pos[0] += DX;
      updScreen(0);
    }
    Serial.print(".");
    if (ebY.left() && pos[1]) {
      pos[1] -= DY;
      updScreen(1);
    }
    Serial.print(".");    
    if (ebY.right() && pos[1] < MAXY) {
      pos[1] += DY;
      updScreen(1);
    }
    Serial.print(".");
    if (ebZ.left() && pos[2]) {
      pos[2]--;
      updScreen(2);
    }
    Serial.print(".");    
    if (ebZ.right() && pos[2] < MAXZ) {
      pos[2]++;
      updScreen(2);
    }
    Serial.print(".");
    if (!digitalRead(BTN)) {
      stX.moveTo(pos[0] * MULT);
      stY.moveTo(pos[1] * MULT);
      while (stX.run() || stY.run());
      delay(300);
      myservo.write(pos[2]);
      delay(300);
      myservo.write(180);
      delay(300);
    }
    Serial.print(".");
  }
  Serial.print("Ок");
}
