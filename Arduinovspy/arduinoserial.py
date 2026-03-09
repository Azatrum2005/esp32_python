import serial
import time

esp32 = serial.Serial('COM10', 115200) 
time.sleep(2)

while(True):
    s=input("enter a string:")
    data_to_send = s
    esp32.write(data_to_send.encode())
    response = esp32.readline().decode().strip()
    print("Response from ESP32:", response[0])
    if s=="break":
        esp32.close()
        break
 