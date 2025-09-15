import re, time, serial
import serial.tools.list_ports

def get_int(ser, tag, tries=10):
    for _ in range(tries):
        ser.write(f"{tag}=?\n".encode())
        line = ser.readline().decode(errors="ignore").strip()
        m = re.search(rf"{tag}=(-?\d+)", line)
        if m: return int(m.group(1))
        time.sleep(0.05)
    raise RuntimeError(f"No reply for {tag}=?")

def stat(ser): return get_int(ser, "STAT")
def epos(ser): return get_int(ser, "EPOS")

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

# 0) Clean slate, closed-loop stage
ser.write(b'RSET=0\n'); time.sleep(0.3)
ser.write(b'XLA1=1250\n'); time.sleep(0.1)
ser.write(b'LOAD=0\n');   time.sleep(0.2)

# 1) Encoder sane + wide limits
ser.write(b'ENCD=1\n')         # ensure encoder is enabled / correct mode for closed loop
ser.write(b'ENCO=0\n')         # clear encoder offset for now
ser.write(b'LLIM=-200000\n')   # very wide (≈ -250 mm at 1.25 µm/count)
ser.write(b'HLIM=200000\n')    # very wide (≈ +250 mm)
ser.write(b'PTO2=400\n'); ser.write(b'PTOL=400\n')   # loose tolerance for homing
time.sleep(0.1)

# 2) Enable force (clear bit4), pick freqs
ser.write(b'ENBL=1\n');   time.sleep(0.1)   # clears ForceZero (bit4) for motion
ser.write(b'FREQ=87000\n'); time.sleep(0.05)
ser.write(b'FRQ2=86000\n'); time.sleep(0.05)

# 3) If an end-stop bit is stuck, choose index direction away from it
s0 = stat(ser)
at_left  = bool(s0 & (1<<14))
at_right = bool(s0 & (1<<15))
indx_dir = 0
if at_left and not at_right:  indx_dir = +1
elif at_right and not at_left: indx_dir = -1
else: indx_dir = 0  # unknown/both → let drive decide

ser.write(b'STAT=?\n') 
time.sleep(0.5) 
status = ser.read(200) 
print(f"Status before index: {status}")

# 4) Index
ser.write(f'INDX={indx_dir}\n'.encode())
if not wait_indexed(ser, timeout=20.0):
    # try opposite once if the first pass didn't catch index
    ser.write(b'INDX=1\n' if indx_dir<=0 else b'INDX=-1\n')
    if not wait_indexed(ser, timeout=20.0):
        raise RuntimeError("Index search stopped without EncoderValid")

ser.write(b'STAT=?\n') 
time.sleep(0.5) 
status = ser.read(200) 
print(f"Status after index: {status}")

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
# 6) Scan from home (closed-loop jog)
ser.write(b'SSPD=2000\n'); time.sleep(0.05)   # 2 mm/s
ser.write(b'SCAN=1\n');   time.sleep(5.0)
ser.write(b'SCAN=0\n')
