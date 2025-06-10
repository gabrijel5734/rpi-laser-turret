# Ta skripta zazna gibanje s pomočjo kamere in pošilja ukaze Arduinu za upravljanje servomotorjev.

import cv2
import numpy as np
import serial
import time
import math

# Parametri za zaznavanje gibanja
history = 500  # Število okvirjev za zgodovino ozadja pri algoritmu MOG2
varThreshold = 100  # Prag variance za zaznavanje gibanja (večji prag pomeni manj občutljivosti)
min_contour_area = 1000  # Minimalna površina konture za veljavno gibanje (filtrira majhne šume)
alpha = 0.5  # Faktor glajenja za eksponentno drseče povprečje središča gibanja
dead_zone_x = 40  # Mrtva cona v pikslih za horizontalno gibanje (preprečuje tresenje servo1)
dead_zone_y = 50  # Mrtva cona v pikslih za vertikalno gibanje (preprečuje tresenje servo2)
threshold_distance = 50  # Največja razdalja v pikslih za glajenje središča (preprečuje skoke)

# Inicializacija kamere z uporabo GStreamer pipeline za Raspberry Pi kamero
cap = cv2.VideoCapture('libcamerasrc ! video/x-raw,width=320,height=240 ! videoconvert ! appsink', cv2.CAP_GSTREAMER)
if not cap.isOpened():
    print("Napaka: Kamera ni dostopna.")  # Izpis napake, če kamera ni dosegljiva
    exit()  # Končaj program, če kamera ne deluje
time.sleep(2.5)  # Počakaj 2,5 sekunde, da se kamera popolnoma inicializira

# Inicializacija ozadja z MOG2 algoritemom za ločevanje ospredja (gibanja) od ozadja
bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=history, varThreshold=varThreshold, detectShadows=False)

# Inicializacija spremenljivk za glajenje središča gibanja (začetno None, dokler ni zaznano gibanje)
smoothed_cX = None
smoothed_cY = None

# Inicializacija serijske povezave z Arduinom prek USB vrat
try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Odpri serijsko povezavo na 9600 baudov
    time.sleep(2)  # Počakaj 2 sekundi, da se povezava stabilizira
except serial.SerialException:
    print("Napaka: Serijska povezava ni na voljo.")  # Izpis napake, če Arduino ni povezan
    exit()  # Končaj program, če povezava ne uspe

# Funkcija za pošiljanje ukazov Arduinu prek serijske povezave
def send_command(command):
    print(f"Pošiljam ukaz: {command}")  # Izpis ukaza v konzolo za sledenje
    ser.write((command + '\n').encode())  # Pošlji ukaz z novo vrstico, kodirano v bajte
    time.sleep(0.05)  # Majhen zamik (50 ms) za zagotavljanje stabilne komunikacije

# Funkcija za zaznavanje središča gibanja v posameznem okvirju
def detect_motion_center(frame, bg_subtractor, min_contour_area):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Pretvori barvni okvir v sivo lestvico
    gray = cv2.GaussianBlur(gray, (5, 5), 0)  # Zamegli sliko z Gaussovim filtrom za zmanjšanje šuma
    fg_mask = bg_subtractor.apply(gray)  # Uporabi MOG2 za ustvarjanje maske ospredja (gibanje)
    kernel = np.ones((5, 5), np.uint8)  # Ustvari 5x5 jedro za morfološke operacije
    fg_mask = cv2.erode(fg_mask, kernel, iterations=1)  # Erozija odstrani majhne šume na maski
    fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)  # Dilatacija poveča območja gibanja
    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # Najdi zunanje konture
    if contours:  # Če so konture najdene
        largest_contour = max(contours, key=cv2.contourArea)  # Izberi največjo konturo po površini
        if cv2.contourArea(largest_contour) > min_contour_area:  # Preveri, ali je kontura dovolj velika
            M = cv2.moments(largest_contour)  # Izračunaj trenutke konture za določitev središča
            if M["m00"] != 0:  # Prepreči deljenje z 0
                cX = int(M["m10"] / M["m00"])  # Izračunaj koordinato X središča
                cY = int(M["m01"] / M["m00"])  # Izračunaj koordinato Y središča
                return (cX, cY), largest_contour  # Vrni središče in največjo konturo
    return None, None  # Vrni None, če ni zaznanega gibanja ali je premajhno

# Glavna zanka za zajemanje videa, zaznavanje gibanja in upravljanje servomotorjev
while True:
    ret, frame = cap.read()  # Preberi naslednji okvir iz kamere
    if not ret:  # Če okvirja ni mogoče prebrati
        print("Napaka: Ni mogoče prebrati okvira.")  # Izpis napake
        break  # Prekini zanko
    
    center_x = frame.shape[1] // 2  # Izračunaj horizontalno središče okvirja (širina / 2)
    center_y = frame.shape[0] // 2  # Izračunaj vertikalno središče okvirja (višina / 2)
    
    center, contour = detect_motion_center(frame, bg_subtractor, min_contour_area)  # Zaznaj gibanje
    
    if center is not None:  # Če je gibanje zaznano
        cX, cY = center  # Pridobi koordinate središča gibanja
        
        # Glajenje središča gibanja z eksponentnim drsečim povprečjem
        if smoothed_cX is None:  # Če je to prvo zaznano gibanje
            smoothed_cX = cX  # Nastavi začetno glajeno vrednost X
            smoothed_cY = cY  # Nastavi začetno glajeno vrednost Y
        else:
            distance = math.sqrt((cX - smoothed_cX)**2 + (cY - smoothed_cY)**2)  # Izračunaj razdaljo do prejšnje točke
            if distance < threshold_distance:  # Če je razdalja znotraj praga, gladi
                smoothed_cX = alpha * cX + (1 - alpha) * smoothed_cX  # Posodobi glajeno X
                smoothed_cY = alpha * cY + (1 - alpha) * smoothed_cY  # Posodobi glajeno Y
            else:
                smoothed_cX = cX  # Če je premik prevelik, uporabi novo vrednost brez glajenja
                smoothed_cY = cY
        
        deviation_x = smoothed_cX - center_x  # Izračunaj odstopanje X od središča okvirja
        deviation_y = smoothed_cY - center_y  # Izračunaj odstopanje Y od središča okvirja
        
        # Upravljanje servo1 za horizontalno gibanje
        if abs(deviation_x) > dead_zone_x:  # Če je odstopanje zunaj mrtve cone
            if deviation_x > 0:  # Če je gibanje desno od središča
                send_command("S1:R")  # Pošlji ukaz za vrtenje servo1 desno
            else:  # Če je gibanje levo od središča
                send_command("S1:L")  # Pošlji ukaz za vrtenje servo1 levo
        else:  # Če je v mrtvi coni
            send_command("S1:S")  # Pošlji ukaz za ustavitev servo1
        
        # Upravljanje servo2 za vertikalno gibanje
        if abs(deviation_y) > dead_zone_y:  # Če je odstopanje zunaj mrtve cone
            if deviation_y > 0:  # Če je gibanje pod središčem
                send_command("S2:D")  # Pošlji ukaz za premik servo2 navzdol
            else:  # Če je gibanje nad središčem
                send_command("S2:U")  # Pošlji ukaz za premik servo2 navzgor
        else:  # Če je v mrtvi coni
            send_command("S2:S")  # Pošlji ukaz za ustavitev servo2
        
        # Vizualizacija: Risanje središča in okvirja gibanja na sliko
        cv2.circle(frame, (int(smoothed_cX), int(smoothed_cY)), 5, (0, 0, 255), -1)  # Nariši rdečo piko na glajenem središču
        x, y, w, h = cv2.boundingRect(contour)  # Pridobi pravokotnik okoli konture gibanja
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)  # Nariši zelen pravokotnik okoli gibanja
        print(f"Središče gibanja: ({int(smoothed_cX)}, {int(smoothed_cY)})")  # Izpis koordinat v konzolo
        cv2.putText(frame, f"X: {int(smoothed_cX)}, Y: {int(smoothed_cY)}", (int(smoothed_cX)+10, int(smoothed_cY)-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)  # Nariši koordinate na sliko
    
    cv2.imshow('Motion Detection', frame)  # Prikaži okvir z vsemi narisanimi elementi
    
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Prekini zanko, če uporabnik pritisne 'q'
        break

cap.release()  # Sprosti kamero po koncu uporabe
cv2.destroyAllWindows()  # Zapri vsa OpenCV okna
ser.close()  # Zapri serijsko povezavo z Arduinom