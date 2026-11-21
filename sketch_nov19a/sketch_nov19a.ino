#include <ESP32Servo.h>

Servo servo;
const int SERVO_PIN = 4;

void setup() {
  servo.attach(SERVO_PIN, 500, 2400);  
  servo.write(0);                
  delay(500);
}

void loop() {
  servo.write(110); 
  delay(2000);     

  servo.write(20);  
  delay(2000);     
}