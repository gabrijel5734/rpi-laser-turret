Projekt za zaznavanje gibanja in upravljanje servomotorjev
Ta projekt uporablja Raspberry Pi in Arduino Nano za zaznavanje gibanja s kamero ter upravljanje dveh servomotorjev. Spodaj so navedene potrebne komponente, povezave in postopek za izgradnjo in zagon.

Potrebne komponente:

Raspberry Pi (npr. Raspberry Pi 4) z nameščenim Raspberry Pi OS
Kamera (RaspberryPi Camera Module 2)
Arduino Nano
Dva servomotorja (SG90):
Servo1: 360-stopinjski servo (horizontalno gibanje)
Servo2: 180-stopinjski servo (vertikalno gibanje)
Varnostni gumb (push-button)
Kabli (za povezavo komponent)
Zunanji napajalnik (za servomotorje, če je potrebno)
USB kabel (za povezavo Arduino Nano z Raspberry Pi)

Povezava strojne opreme
1. Kamera na Raspberry Pi

Priključite kamero na CSI port Raspberry Pi.
Omogočite kamero:sudo raspi-config

Pojdite na "Interfacing Options" > "Camera" > "Enable".

2. Servomotorji na Arduino Nano

Servo1 (360-stopinjski):
Signalni pin: D9
Napajalni pin: 5V na Arduino Nano ali zunanji napajalnik
Ozemljitveni pin: GND


Servo2 (180-stopinjski):
Signalni pin: D10
Napajalni pin: 5V na Arduino Nano ali zunanji napajalnik
Ozemljitveni pin: GND



3. Varnostni gumb na Arduino Nano

Ena stran: D2
Druga stran: GND
Uporabljen je notranji pull-up upor.

4. Arduino Nano na Raspberry Pi

Povežite prek USB kabla (npr. /dev/ttyUSB0).

Potrebne knjižnice za Raspberry Pi
Python skripta motion_detection_debelinko.py zahteva:

opencv-python (obdelava videa)
numpy (numerični izračuni)
pyserial (serijska komunikacija)
time in math (standardni knjižnici)

Namestitev knjižnic

Posodobite pakete:sudo apt-get update


Namestite OpenCV:sudo apt-get install python3-opencv


Namestite NumPy in pyserial:pip3 install numpy pyserial

Postopek namestitve in zagon
1. Nalaganje kode na Arduino Nano

Namestite Arduino IDE.
Odprite rpiprojektkontrolaservo.ino.
Izberite COM port (npr. /dev/ttyUSB0).
Naložite kodo.

2. Priprava Raspberry Pi

Preverite povezavo kamere in Arduina.
Kopirajte motion_detection_debelinko.py na Raspberry Pi.

3. Zagon projekta

Odprite terminal.
Pomaknite se v mapo s skripto.
Zaženite:python3 motion_detection_debelinko.py
