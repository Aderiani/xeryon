import serial
import time

# Via USB
ser = serial.Serial('COM6', 9600, timeout=1)
ser.write(b'UART=9600\n')
time.sleep(0.5)
ser.write(b'SAVE\n')  # Save settings to memory
time.sleep(1)
print("Settings saved")
ser.close()