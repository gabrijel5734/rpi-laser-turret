#include <Servo.h>

Servo servo1; // 360-stopinjski servo
Servo servo2; // 180-stopinjski servo

const int safetyButtonPin = 2; // Pin za varnostni gumb

// Začetne pozicije in omejitve
int servo1Position = 0; // Približna pozicija v stopinjah
const int servo1InitialPosition = 0;
const int servo1MaxRotation = 100; // ±100 stopinj
const int servo1Speed = 15; // Hitrost vrtenja v stopinjah na sekundo
unsigned long previousMillis = 0;
const long interval = 50; // Interval za posodobitev pozicije (100ms)

int servo2CurrentAngle = 90; // Trenutni kot servo2
const int servo2Step = 1; // Korak premika v stopinjah
const int servo2Delay = 20; // Zamik med koraki (ms)

bool servo1Rotating = false;
int servo1Direction = 0; // 1 za desno, -1 za levo, 0 za ustavljeno

void setup() {
  Serial.begin(9600);
  servo1.attach(9);  // Servo1 na pinu D9
  servo2.attach(10); // Servo2 na pinu D10
  pinMode(safetyButtonPin, INPUT_PULLUP); // Gumb z notranjim pull-up uporom
  servo1.writeMicroseconds(1500); // Ustavitev servo1
  servo2.write(servo2CurrentAngle); // Nastavitev začetnega kota servo2
  Serial.println("Servo1 na 0, Servo2 na 90");
}

void loop() {
  unsigned long currentMillis = millis();
  
  if (digitalRead(safetyButtonPin) == LOW) { // Če je gumb pritisnjen
    servo1.writeMicroseconds(1500); // Ustavitev servo1
    servo2.write(servo2CurrentAngle); // Ohranitev trenutnega kota servo2
    servo1Rotating = false;
    Serial.println("Varnostni gumb pritisnjen, servoja ustavljena");
    delay(100); // Preprečitev preobremenitve procesorja
  } else {
    if (Serial.available() > 0) {
      String command = Serial.readStringUntil('\n');
      command.trim(); // Odstranitev odvečnih presledkov ali novih vrstic
      if (command.startsWith("S1:")) {
        String direction = command.substring(3);
        if (direction == "R") {
          if (servo1Position < servo1InitialPosition + servo1MaxRotation) {
            servo1.writeMicroseconds(1500 + (servo1Speed * 10)); // Vrtenje desno
            servo1Rotating = true;
            servo1Direction = 1;
          } else {
            servo1.writeMicroseconds(1500); // Ustavitev
            servo1Rotating = false;
            Serial.println("Dosežena meja +100 stopinj za Servo1");
          }
        } else if (direction == "L") {
          if (servo1Position > servo1InitialPosition - servo1MaxRotation) {
            servo1.writeMicroseconds(1500 - (servo1Speed * 10)); // Vrtenje levo
            servo1Rotating = true;
            servo1Direction = -1;
          } else {
            servo1.writeMicroseconds(1500); // Ustavitev
            servo1Rotating = false;
            Serial.println("Dosežena meja -100 stopinj za Servo1");
          }
        } else if (direction == "S") {
          servo1.writeMicroseconds(1500); // Ustavitev
          servo1Rotating = false;
        } else {
          Serial.println("Neznan ukaz za Servo1");
        }
      } else if (command.startsWith("S2:")) {
        String direction = command.substring(3);
        if (direction == "U") {
          if (servo2CurrentAngle < 180) {
            servo2CurrentAngle += servo2Step;
            servo2.write(servo2CurrentAngle);
            delay(servo2Delay);
          } else {
            Serial.println("Dosežena zgornja meja za Servo2");
          }
        } else if (direction == "D") {
          if (servo2CurrentAngle > 0) {
            servo2CurrentAngle -= servo2Step;
            servo2.write(servo2CurrentAngle);
            delay(servo2Delay);
          } else {
            Serial.println("Dosežena spodnja meja za Servo2");
          }
        } else if (direction == "S") {
          // Ustavitev ni potrebna, saj se servo ustavi, ko ni ukaza
        } else {
          Serial.println("Neznan ukaz za Servo2");
        }
      } else {
        Serial.println("Neznan ukaz");
      }
    }
    
    // Posodobitev pozicije servo1 vsakih 100ms, če se vrti
    if (servo1Rotating && currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis;
      // Izračun premika v stopinjah (hitrost * čas)
      float timeElapsed = interval / 1000.0; // v sekundah
      int delta = servo1Speed * timeElapsed * servo1Direction;
      servo1Position += delta;
      
      // Preverjanje omejitve
      if (servo1Position > servo1InitialPosition + servo1MaxRotation || servo1Position < servo1InitialPosition - servo1MaxRotation) {
        servo1.writeMicroseconds(1500); // Ustavitev
        servo1Rotating = false;
        Serial.println("Dosežena omejitev za Servo1");
      }
    }
  }
}