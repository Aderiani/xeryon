import serial
import time

ser = serial.Serial('COM10', 9600, timeout=2)
time.sleep(1)

# Full reset sequence
ser.write(b'RSET\n')
time.sleep(2)

# Configure stage type
ser.write(b'XLA3=1250\n')
time.sleep(1)

# Load settings
ser.write(b'LOAD\n')
time.sleep(0.5)

# Set motor parameters
ser.write(b'VOLT=48000\n')  # 48V
ser.write(b'FREQ=87000\n')
ser.write(b'AMPL=45\n')
ser.write(b'ENBL=1\n')
time.sleep(0.5)

# Find index first (required for closed-loop)
print("Finding index...")
ser.write(b'INDX=0\n')
time.sleep(5)

# Check if encoder is valid
ser.write(b'STAT=?\n')
time.sleep(0.5)
status = ser.read(200)
print(f"Status after index: {status}")

# Try movement
print("Moving...")
ser.write(b'DPOS=5000\n')
time.sleep(3)

ser.write(b'EPOS=?\n')
time.sleep(0.5)
print(f"Position: {ser.read(100)}")

ser.close()