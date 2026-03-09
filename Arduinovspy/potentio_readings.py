import serial
import time

try:
    esp32 = serial.Serial('COM10', 115200, timeout=1)
    time.sleep(2) 

    while True:
        line = esp32.readline().decode().strip() 
        if not line:
            continue 
        if line.startswith('1'):
            adc1 = int(line[1:]) 
            print("ADC1:", adc1)
        elif line.startswith('2'):
            adc2 = int(line[1:])
            print("ADC2:", adc2)

except KeyboardInterrupt:
    print("\nKeyboard Interrupt detected")

finally:
    if 'esp32' in locals() and esp32.is_open:
        esp32.close()
