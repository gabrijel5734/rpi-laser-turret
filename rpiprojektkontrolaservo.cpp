// Ta skripta upravlja dva servomotorja na podlagi ukazov iz serijske povezave.
// Servo1 je 360-stopinjski servo za horizontalno gibanje.
// Servo2 je 180-stopinjski servo za vertikalno gibanje.

#include <Servo.h>

Servo servo1; // Objekt za 360-stopinjski servo (horizontalno gibanje)
Servo servo2; // Objekt za 180-stopinjski servo (vertikalno gibanje)

const int safetyButtonPin = 2; // Digitalni pin za varnostni gumb (pritisk ustavi vse servomotorje)

// Spremenljivke za sledenje položaju in omejitvam servo1 (360-stopinjski servo)
int servo1Position = 0; // Trenutna približna pozicija servo1 v stopinjah (sledi vrtenju)
const int servo1InitialPosition = 0; // Začetna pozicija servo1 (referenčna točka)
const int servo1MaxRotation = 100; // Največje dovoljeno vrtenje servo1 (±100 stopinj od začetne pozicije)
const int servo1Speed = 15; // Hitrost vrtenja servo1 v stopinjah na sekundo
unsigned long previousMillis = 0; // Časovnik za sledenje zadnje posodobitve položaja servo1
const long interval = 50; // Interval posodabljanja pozicije servo1 v milisekundah (50 ms)

// Spremenljivke za upravljanje servo2 (180-stopinjski servo)
int servo2CurrentAngle = 90; // Trenutni kot servo2 v stopinjah (začetna pozicija 90°)
const int servo2Step = 1; // Korak premika servo2 v stopinjah za gladko gibanje
const int servo2Delay = 20; // Zamik v milisekundah med posameznimi koraki servo2

bool servo1Rotating = false; // Stanje servo1: ali se trenutno vrti
int servo1Direction = 0; // Smer vrtenja servo1: 1 (desno), -1 (levo), 0 (ustavljen)

void setup() {
  Serial.begin(9600); // Začni serijsko komunikacijo z Raspberry Pi na 9600 baudov
  servo1.attach(9);  // Poveži servo1 z digitalnim pinom D9
  servo2.attach(10); // Poveži servo2 z digitalnim pinom D10
  pinMode(safetyButtonPin, INPUT_PULLUP); // Nastavi pin za varnostni gumb z notranjim pull-up uporom
  servo1.writeMicroseconds(1500); // Nastavi servo1 na nevtralno pozicijo (1500 µs = ustavljen)
  servo2.write(servo2CurrentAngle); // Nastavi servo2 na začetni kot 90 stopinj
  Serial.println("Servo1 na 0, Servo2 na 90"); // Izpis začetnega stanja v serijski monitor
}

void loop() {
  unsigned long currentMillis = millis(); // Pridobi trenutni čas v milisekundah
  
  if (digitalRead(safetyButtonPin) == LOW) { // Če je varnostni gumb pritisnjen (LOW zaradi pull-up)
    servo1.writeMicroseconds(1500); // Takoj ustavi servo1
    servo2.write(servo2CurrentAngle); // Ohrani trenutni kot servo2
    servo1Rotating = false; // Označi, da se servo1 ne vrti
    Serial.println("Varnostni gumb pritisnjen, servoja ustavljena"); // Izpis obvestila
    delay(100); // Majhen zamik za preprečitev preobremenitve procesorja
  } else { // Če gumb ni pritisnjen, nadaljuj z običajnim delovanjem
    if (Serial.available() > 0) { // Preveri, ali so na voljo podatki prek serijske povezave
      String command = Serial.readStringUntil('\n'); // Preberi ukaz do konca vrstice
      command.trim(); // Odstrani morebitne odvečne presledke ali znake
      if (command.startsWith("S1:")) { // Če je ukaz namenjen servo1 (horizontalno)
        String direction = command.substring(3); // Izvleci smer ukaza (npr. "R", "L", "S")
        if (direction == "R") { // Ukaz za vrtenje servo1 desno
          if (servo1Position < servo1InitialPosition + servo1MaxRotation) { // Preveri, ali je znotraj omejitve
            servo1.writeMicroseconds(1500 + (servo1Speed * 10)); // Vrti desno (več kot 1500 µs)
            servo1Rotating = true; // Označi, da se servo1 vrti
            servo1Direction = 1; // Nastavi smer vrtenja na desno
          } else { // Če je dosežena omejitev
            servo1.writeMicroseconds(1500); // Ustavitev servo1
            servo1Rotating = false; // Označi, da se ne vrti več
            Serial.println("Dosežena meja +100 stopinj za Servo1"); // Izpis obvestila
          }
        } else if (direction == "L") { // Ukaz za vrtenje servo1 levo
          if (servo1Position > servo1InitialPosition - servo1MaxRotation) { // Preveri, ali je znotraj omejitve
            servo1.writeMicroseconds(1500 - (servo1Speed * 10)); // Vrti levo (manj kot 1500 µs)
            servo1Rotating = true; // Označi, da se servo1 vrti
            servo1Direction = -1; // Nastavi smer vrtenja na levo
          } else { // Če je dosežena omejitev
            servo1.writeMicroseconds(1500); // Ustavitev servo1
            servo1Rotating = false; // Označi, da se ne vrti več
            Serial.println("Dosežena meja -100 stopinj za Servo1"); // Izpis obvestila
          }
        } else if (direction == "S") { // Ukaz za ustavitev servo1
          servo1.writeMicroseconds(1500); // Nastavi nevtralno pozicijo (ustavljen)
          servo1Rotating = false; // Označi, da se servo1 ne vrti
        } else { // Če je ukaz neznan
          Serial.println("Neznan ukaz za Servo1"); // Izpis napake
        }
      } else if (command.startsWith("S2:")) { // Če je ukaz namenjen servo2 (vertikalno)
        String direction = command.substring(3); // Izvleci smer ukaza (npr. "U", "D", "S")
        if (direction == "U") { // Ukaz za premik servo2 navzgor
          if (servo2CurrentAngle < 180) { // Preveri, ali je kot znotraj omejitve 0-180°
            servo2CurrentAngle += servo2Step; // Povečaj kot za en korak
            servo2.write(servo2CurrentAngle); // Nastavi nov kot servo2
            delay(servo2Delay); // Počakaj kratek čas za gladko gibanje
          } else { // Če je dosežena zgornja meja
            Serial.println("Dosežena zgornja meja za Servo2"); // Izpis obvestila
          }
        } else if (direction == "D") { // Ukaz za premik servo2 navzdol
          if (servo2CurrentAngle > 0) { // Preveri, ali je kot znotraj omejitve 0-180°
            servo2CurrentAngle -= servo2Step; // Zmanjšaj kot za en korak
            servo2.write(servo2CurrentAngle); // Nastavi nov kot servo2
            delay(servo2Delay); // Počakaj kratek čas za gladko gibanje
          } else { // Če je dosežena spodnja meja
            Serial.println("Dosežena spodnja meja za Servo2"); // Izpis obvestila
          }
        } else if (direction == "S") { // Ukaz za ustavitev servo2
          // Ni potrebna akcija, saj servo2 ostane na trenutnem kotu, ko ni ukaza
        } else { // Če je ukaz neznan
          Serial.println("Neznan ukaz za Servo2"); // Izpis napake
        }
      } else { // Če ukaz ne ustreza nobenemu servomotorju
        Serial.println("Neznan ukaz"); // Izpis napake
      }
    }
    
    // Posodobitev pozicije servo1, če se vrti (sledenje približnemu kotu)
    if (servo1Rotating && currentMillis - previousMillis >= interval) { // Če je čas za posodobitev
      previousMillis = currentMillis; // Posodobi čas zadnje posodobitve
      float timeElapsed = interval / 1000.0; // Pretvori interval v sekunde
      int delta = servo1Speed * timeElapsed * servo1Direction; // Izračunaj premik v stopinjah
      servo1Position += delta; // Posodobi trenutno pozicijo servo1
      
      // Preveri, ali je servo1 dosegel omejitev vrtenja
      if (servo1Position > servo1InitialPosition + servo1MaxRotation || servo1Position < servo1InitialPosition - servo1MaxRotation) {
        servo1.writeMicroseconds(1500); // Ustavitev servo1, če je prekoračena omejitev
        servo1Rotating = false; // Označi, da se ne vrti več
        Serial.println("Dosežena omejitev za Servo1"); // Izpis obvestila
      }
    }
  }
}