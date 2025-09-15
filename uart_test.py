import serial
# print(serial.__file__)
import time
import serial.tools.list_ports

ser = serial.Serial('COM6', 9600, timeout=2)
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
ser.write(b'VOLT=48000\n')  # 48V VOLT is open loop specific command
ser.write(b'FREQ=87000\n')  # FREQ is closed loop specific command
ser.write(b'AMPL=45\n')     # AMPL is open loop specific command
ser.write(b'ENBL=1\n')      # ENBL is open/closed loop specific command
ser.write(b'INFO=0\n')      # stop broadcasting
time.sleep(0.5)

ser.write(b'SAVE\n')  # Save above settings to memory

#check the settings
ser.write(b'ENBL=?\n')
time.sleep(0.5) 
print(f"Enbale status: {ser.read(200)}")
ser.write(b'FREQ=?\n')
time.sleep(0.5) 
print(f"Freq check: {ser.read(200)}")
ser.write(b'SOFT=?\n')      #request software number
time.sleep(0.5)
print(f"Software number: {ser.read(200)}")
ser.write(b'SRNO=?\n')      #request serial number
time.sleep(0.5)
print(f"Serial number: {ser.read(200)}")
ser.write(b'ENON=?\n')      #check for open or closed loop ,ENON is closed loop command. so not receiving valid response
time.sleep(0.5)
print(f"Opeloop or Closed loop: {ser.read(200)}")
ser.write(b'STAT=?\n')      #Check the status bits
time.sleep(0.5)
print(f"Status of STAT: {ser.read(200)}")


# # Find index first (required for closed-loop)
# print("Finding index...")
# ser.write(b'INDX=0\n')
# time.sleep(5)

# set a reasonable jog speed: 5 mm/s = 5000 µm/s
ser.write(b'SSPD=2000\n')        # speed for scanning/jogging in open loop
time.sleep(0.1)

#start moving
print("Start Moving*********\n")
ser.write(b'SCAN=1\n')     
time.sleep(5.0)
ser.write(b'SCAN=0\n') 
time.sleep(1.0)
ser.write(b'SCAN=-1\n')     
time.sleep(5.0)
ser.write(b'SCAN=0\n') 


# # Check if encoder is valid
# ser.write(b'STAT=?\n')
# time.sleep(0.5)
# status = ser.read(200)
# print(f"Status after index: {status}")

# # Try movement
# print("Moving...")
# ser.write(b'DPOS=5000\n')
# time.sleep(3)

# ser.write(b'EPOS=?\n')
# time.sleep(0.5)
# print(f"Position: {ser.read(100)}")

ser.close()