import re, time, serial
import serial.tools.list_ports
# from readsetting import read_many
# from readsetting import print_kv_table
# from readsetting import READBACK_TAGS

def writesetting():
    ser.write(b'ENCD=0\n'); time.sleep(0.05)         # encoder direction
    ser.write(b'ENCO=-706\n'); time.sleep(0.05)         # clear encoder offset for now
    ser.write(b'LLIM=-75\n'); time.sleep(0.05)   # very wide (≈ -250 mm at 1.25 µm/count)
    ser.write(b'HLIM=75\n') ; time.sleep(0.05)   # very wide (≈ +250 mm)
    ser.write(b'PTO2=4\n'); ser.write(b'PTOL=2\n')   # loose tolerance for homing
    ser.write(b'TOUT=1000\n'); ser.write(b'TOU2=60\n') #safety timeouts
    #The zones are defined symmetrically around the target position, with zone 1 being the area closest to the target and zone 2 the widest.
    ser.write(b'ZON1=0.01\n'); ser.write(b'ZON2=1\n') ; time.sleep(0.02)
    ser.write(b'PROP=120\n'); ser.write(b'PRO2=40\n') ; time.sleep(0.02)
    ser.write(b'FREQ=87000\n'); time.sleep(0.05)
    ser.write(b'FRQ2=86000\n'); time.sleep(0.05)
    ser.write(b'HFRQ=88000\n'); ser.write(b'LFRQ=82500\n');time.sleep(0.05)
    ser.write(b'POLI=97\n');
    ser.write(b'ENBL=1\n'); time.sleep(0.05)
    time.sleep(0.1)


def get_int(ser, tag, tries=10):
    for _ in range(tries):
        ser.reset_input_buffer()  
        ser.write(f"{tag}=?\n".encode())
        time.sleep(0.06)    
        line = ser.readline().decode(errors="ignore").strip()
        m = re.search(rf"{tag}=(-?\d+)", line)
        if m: return int(m.group(1))
        time.sleep(0.05)
    raise RuntimeError(f"No reply for {tag}=?")

def stat(ser): return get_int(ser, "STAT")
def epos(ser): return get_int(ser, "EPOS")

#Usage - print("Pre-index STAT:", stat(), bits(stat()))
def bits(s):  # for debugging
    return {b: bool(s & (1<<b)) for b in (4,5,6,7,8,9,10,13,14,15)}

def wait_indexed(ser, timeout=20.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = stat(ser)
        enc_valid = bool(s & (1<<8))   # EncoderValid
        searching = bool(s & (1<<9))   # SearchingIndex
        scanning  = bool(s & (1<<13))  # Scanning
        if enc_valid: return True
        if not searching and scanning:  # still moving → let it settle
            time.sleep(0.2); continue
        if not searching and not scanning and not enc_valid:
            return False
        time.sleep(0.05)
    return False

def wait_pos(ser, target, pto2=400, timeout=12.0):
    t0 = time.time(); ok_streak = 0
    while time.time() - t0 < timeout:
        s = stat(ser)
        at_target = abs(epos(ser) - target) <= pto2
        reached = bool(s & (1<<10))   # PositionReached
        if at_target or reached:
            ok_streak += 1
            if ok_streak >= 4: return True
        else:
            ok_streak = 0
        time.sleep(0.05)
    return False


ser = serial.Serial('COM6', 9600, timeout=0.5)
time.sleep(0.3)

ser.reset_input_buffer(); ser.reset_output_buffer()

# 0) Clean slate, closed-loop stage
ser.write(b'RSET=0\n'); time.sleep(0.3)
# ser.write(b'XLA1=1250\n'); time.sleep(0.1)
ser.write(b'LOAD=0\n');   time.sleep(0.2)
ser.write(b'INFO=0\n');   time.sleep(0.2) #stop broadcasting
# print("Sending the setting\n")
# writesetting()
# time.sleep(0.3)
# print("Settings applied\n")

# old = read_many(READBACK_TAGS)
# print_kv_table(old, "Current settings (after LOAD)")

print("Scanning ---------------")

ser.write(b'SCAN=-1\n');time.sleep(5.0)
ser.write(b'SCAN=0\n');time.sleep(0.2)
ser.write(b'SCAN=1\n');time.sleep(5.0)
ser.write(b'SCAN=0\n');time.sleep(0.2)

# ser.write(b'SAVE\n'); time.sleep(0.05)  # Save above settings to memory

# 3) If an end-stop bit is stuck, choose index direction away from it
s0 = stat(ser)
at_left  = bool(s0 & (1<<14))
at_right = bool(s0 & (1<<15))
indx_dir = 0
if at_left and not at_right:  indx_dir = +1
elif at_right and not at_left: indx_dir = -1
else: indx_dir = 0  # unknown/both → let drive decide

# ser.write(b'SSPD=20000\n'); time.sleep(0.05)   # 2 mm/s
if at_left:
    # print("At left\n")    
    ser.write(b'SCAN=1\n');time.sleep(5.0)
    ser.write(b'SCAN=0\n');time.sleep(0.2)
    print("Scanning-----")

if at_right:
    # print("At Right\n")    
    ser.write(b'SCAN=-1\n');time.sleep(5.0)
    ser.write(b'SCAN=0\n');time.sleep(0.2)
    print("Scanning-----")

# ser.write(b'STAT=?\n') 
# time.sleep(0.5) 
# status = ser.read(200) 
# print(f"Status before index: {status}")

print("Pre-index STAT:", stat(ser), bits(stat(ser)))

ser.write(b'ENBL=1\n')
time.sleep(0.1)  #just before index

print("Finding the index\n")
ser.write(f'INDX={indx_dir}\n'.encode())

if not wait_indexed(ser, timeout=20.0):
    # try opposite once if the first pass didn't catch index
    ser.write(b'INDX=1\n' if indx_dir<=0 else b'INDX=-1\n')
    enc_valid = bool(s0 & (1<<8))   # EncoderValid
    print("Looking for encoder valid")
    if(enc_valid):
        print("Index found")        
    if not wait_indexed(ser, timeout=20.0):
        raise RuntimeError("Index search stopped without EncoderValid")

# ser.write(b'STAT=?\n') 
# time.sleep(0.5) 
# status = ser.read(200) 
# print(f"Status after index: {status}")

print("Post-index STAT:", stat(ser), bits(stat(ser)))

# 5) Home to 0 counts
ser.write(b'SCAN=0\n'); time.sleep(0.05)   # make sure no jog is active
ser.write(b'ENBL=1\n'); time.sleep(0.05)   # re-clear any forced zero
ser.write(b'DPOS=0\n')
if not wait_pos(ser, 0, pto2=400, timeout=12.0):
    # nudge and try once more if we were right on a soft limit edge
    ser.write(b'SSPD=1500\n'); time.sleep(0.05)  # 1.5 mm/s
    ser.write(b'SCAN=1\n'); time.sleep(0.3); ser.write(b'SCAN=0\n'); time.sleep(0.1)
    ser.write(b'DPOS=0\n')
    if not wait_pos(ser, 0, pto2=400, timeout=12.0):
        raise RuntimeError("Failed to reach home (0 counts)")

print(f"Reached to home postion\n")

ser.write(b'STAT=?\n') 
time.sleep(0.5) 
status = ser.read(200) 
print(f"Status after home position: {status}")

ser.write(b'EPOS=?\n') 
time.sleep(0.5) 
status = ser.read(200) 
print(f"EPOS after home position: {status}")

# 6) Scan from home (closed-loop jog)
ser.write(b'SSPD=2000\n'); time.sleep(0.05)   # 2 mm/s
ser.write(b'SCAN=1\n');   time.sleep(5.0)
ser.write(b'SCAN=0\n')

 # Try movement
print("Moving...")
ser.write(b'DPOS=15500\n') #1 count = 0.00125 mm . Multiply and get the EPOS and DPOS In MM
time.sleep(3)
ser.write(b'WAIT=100\n')
ser.write(b'EPOS=?\n')
time.sleep(0.5)
print(f"Position: {ser.read(100)}")

ser.write(b'DPOS=0\n') #1 count = 0.00125 mm . Multiply and get the EPOS and DPOS In MM
time.sleep(3)
ser.write(b'WAIT=100\n')

ser.write(b'EPOS=?\n')
time.sleep(0.5)
ser.write(b'WAIT=100\n')
print(f"Position: {ser.read(100)}")

ser.write(b'DPOS= -15500\n') #1 count = 0.00125 mm . Multiply and get the EPOS and DPOS In MM
time.sleep(3.0)
ser.write(b'WAIT=100\n')

ser.write(b'EPOS=?\n')
time.sleep(0.5)
print(f"Position: {ser.read(100)}")