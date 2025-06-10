import cv2
import numpy as np
import serial
import time
import math

# Parametri
history = 500
varThreshold = 100  # Povečan za manj občutljivo zaznavanje
min_contour_area = 1000  # Povečan za filtriranje šuma
alpha = 0.5
dead_zone_x = 40
dead_zone_y = 50
threshold_distance = 50  # Razdalja za vztrajnost sledenja

# Inicializacija kamere
cap = cv2.VideoCapture('libcamerasrc ! video/x-raw,width=320,height=240 ! videoconvert ! appsink', cv2.CAP_GSTREAMER)
if not cap.isOpened():
    print("Napaka: Kamera ni dostopna.")
    exit()

time.sleep(2.5)

bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=history, varThreshold=varThreshold, detectShadows=False)

smoothed_cX = None
smoothed_cY = None

try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    time.sleep(2)
except serial.SerialException:
    print("Napaka: Serijska povezava ni na voljo.")
    exit()

def send_command(command):
    print(f"Pošiljam ukaz: {command}")
    ser.write((command + '\n').encode())
    time.sleep(0.05)

def detect_motion_center(frame, bg_subtractor, min_contour_area):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)  # Dodano za zmanjšanje šuma
    fg_mask = bg_subtractor.apply(gray)
    kernel = np.ones((5, 5), np.uint8)
    fg_mask = cv2.erode(fg_mask, kernel, iterations=1)
    fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)
    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) > min_contour_area:
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                return (cX, cY), largest_contour
    return None, None

while True:
    ret, frame = cap.read()
    if not ret:
        print("Napaka: Ni mogoče prebrati okvira.")
        break
    
    center_x = frame.shape[1] // 2
    center_y = frame.shape[0] // 2
    
    center, contour = detect_motion_center(frame, bg_subtractor, min_contour_area)
    
    if center is not None:
        cX, cY = center
        
        if smoothed_cX is None:
            smoothed_cX = cX
            smoothed_cY = cY
        else:
            distance = math.sqrt((cX - smoothed_cX)**2 + (cY - smoothed_cY)**2)
            if distance < threshold_distance:
                smoothed_cX = alpha * cX + (1 - alpha) * smoothed_cX
                smoothed_cY = alpha * cY + (1 - alpha) * smoothed_cY
            else:
                smoothed_cX = cX
                smoothed_cY = cY
        
        deviation_x = smoothed_cX - center_x
        deviation_y = smoothed_cY - center_y
        
        if abs(deviation_x) > dead_zone_x:
            if deviation_x > 0:
                send_command("S1:R")
            else:
                send_command("S1:L")
        else:
            send_command("S1:S")
        
        if abs(deviation_y) > dead_zone_y:
            if deviation_y > 0:
                send_command("S2:D")
            else:
                send_command("S2:U")
        else:
            send_command("S2:S")
        
        cv2.circle(frame, (int(smoothed_cX), int(smoothed_cY)), 5, (0, 0, 255), -1)
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        print(f"Središče gibanja: ({int(smoothed_cX)}, {int(smoothed_cY)})")
        cv2.putText(frame, f"X: {int(smoothed_cX)}, Y: {int(smoothed_cY)}", (int(smoothed_cX)+10, int(smoothed_cY)-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    cv2.imshow('Motion Detection', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
ser.close()