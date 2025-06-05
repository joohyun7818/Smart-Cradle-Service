#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <Servo.h>

Adafruit_MLX90614 mlx = Adafruit_MLX90614();
Servo myServo;
String command = "";
bool isServoActive = false;

void setup() {
  Serial.begin(9600);
  mlx.begin();
  myServo.attach(9); 
}

void loop() {
  // 체온 센서 데이터 전송
  float temperature = mlx.readObjectTempC();
  Serial.print("아기 체온:");
  Serial.print(temperature);
  Serial.println("°C");

  // 시리얼 명령 처리
  if (Serial.available()) {
    command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "servo") {
      isServoActive = true;
    } else if (command == "stop") {
      isServoActive = false;
    }
  }

  // 모터 제어
  if (isServoActive) {
    myServo.writeMicroseconds(1450);
    delay(500);
    myServo.writeMicroseconds(1550);
    delay(500);
  } else {
    myServo.writeMicroseconds(1500); // 중립 위치
  }

  delay(1000); // 1초 대기
}
