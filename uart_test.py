import re, time, serial ,math
import serial.tools.list_ports

RES_MM_PER_COUNT = 0.00125  # 1250 nm/count encoder resolution

def counts_to_mm(counts):
    return counts * RES_MM_PER_COUNT
#usage
#print(f"EPOS is : {counts_to_mm(5500):.6f} mm")

def mm_to_counts(mm):
    return int(round(mm / RES_MM_PER_COUNT))

def writesetting():
    ser.write(b'ENCD=0\n'); time.sleep(0.05)         # encoder direction
    ser.write(b'ENCO=-706\n'); time.sleep(0.05)         # clear encoder offset for now
    ser.write(b'LLIM=-60000\n'); time.sleep(0.05)   # very wide (≈ -250 mm at 1.25 µm/count)
    ser.write(b'HLIM=60000\n') ; time.sleep(0.05)   # very wide (≈ +250 mm)
    ser.write(b'PTO2=4\n'); ser.write(b'PTOL=2\n')   # loose tolerance for homing
    ser.write(b'TOUT=1000\n'); ser.write(b'TOU2=60\n') #safety timeouts
    #The zones are defined symmetrically around the target position, with zone 1 being the area closest to the target and zone 2 the widest.
    ser.write(b'ZON1=0.01\n'); ser.write(b'ZON2=1\n') ; time.sleep(0.02)
    ser.write(b'PROP=120\n'); ser.write(b'PRO2=40\n') ; time.sleep(0.02)
    ser.write(b'FREQ=87000\n'); time.sleep(0.05)
    ser.write(b'FRQ2=86000\n'); time.sleep(0.05)
    ser.write(b'HFRQ=88000\n'); ser.write(b'LFRQ=82500\n');time.sleep(0.05)
    ser.write(b'POLI=100\n');
    ser.write(b'ISPD=10000\n');
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
        # if at_target or reached:
        if at_target and reached:    
            ok_streak += 1
            if ok_streak >= 4: return True
        else:
            ok_streak = 0
        time.sleep(0.05)
    return False

def _read_tag_int(ser, tag: bytes, prefix: bytes = b"", window=1.0):
    """Read a TAG=number line within 'window' seconds. Returns int or None."""
    t0 = time.time()
    while time.time() - t0 < window:
        line = ser.readline()
        if not line:
            continue
        s = line.strip()
        # Accept both single-axis ("TAG=...") and multi-axis ("X:TAG=...")
        if prefix and s.startswith(prefix):
            s = s[len(prefix):]
        if s.startswith(tag + b"="):
            try:
                return int(s.split(b"=", 1)[1])
            except ValueError:
                return None
    return None


ser = serial.Serial('COM6', 9600, timeout=0.5)
time.sleep(0.3)

ser.reset_input_buffer(); ser.reset_output_buffer()

ser.write(b'RSET=0\n'); time.sleep(0.3)
# ser.write(b'XLA1=1250\n'); time.sleep(0.1)
ser.write(b'LOAD=0\n');   time.sleep(0.2)
ser.write(b'INFO=0\n');   time.sleep(0.2) #stop broadcasting
print("Sending the setting\n")
writesetting()
time.sleep(0.3)
print("Settings applied\n")
ser.write(b'WAIT=100\n')
#Get the limits values 
ser.write(b'LLIM=?\n');time.sleep(0.2) 
llim = _read_tag_int(ser, b"LLIM")
print(f"LLIM status: {llim * RES_MM_PER_COUNT } mm")
ser.write(b'HLIM=?\n');time.sleep(0.2) 
hlim = _read_tag_int(ser, b"HLIM")
print(f"HLIM status: {hlim * RES_MM_PER_COUNT } mm")
#get the ENCO value -: distance between the index position and the desired zero position,in encoder units. 
ser.write(b'ENCO=?\n');time.sleep(0.2) 
enco = _read_tag_int(ser, b"ENCO")
print(f"ENCO status: {enco} counts {enco * RES_MM_PER_COUNT } mm")

ser.write(b'ENBR=?\n');time.sleep(0.2) 
enbr = _read_tag_int(ser, b"ENBR")
print(f"ENBR status: {enbr}")

ser.write(b'SSPD=?\n');time.sleep(0.2) 
sspd = _read_tag_int(ser, b"SSPD")
print(f"SSPD status: {sspd} ")

ser.write(b'SSPD=5000\n'); time.sleep(0.05) 

ser.write(b'SSPD=?\n');time.sleep(0.2) 
sspd = _read_tag_int(ser, b"SSPD")
print(f"SSPD status after setting value: {sspd} ")

ser.write(b'SPCF=0\n');time.sleep(0.2) 
ser.write(b'SPCF=?\n');time.sleep(0.2) 
spcf = _read_tag_int(ser, b"SPCF")
print(f"spcf status after setting value: {spcf} ")

ser.write(b'ISPD=?\n');time.sleep(0.2) 
ispd = _read_tag_int(ser, b"ISPD")
print(f"ispd status after setting value: {ispd} ")

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

ser.write(b'SSPD=5000\n'); time.sleep(0.05)   # 2 mm/s
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
print(f"INDX={indx_dir}\n")

ser.write(b'ENBL=1\n') ; time.sleep(0.12)  #just before index

print("Finding the index\n")
ser.write(b'SSPD=5000\n'); time.sleep(0.05)
ser.write(b'SSPD=?\n');time.sleep(0.2) 
sspd = _read_tag_int(ser, b"SSPD")
print(f"SSPD status after setting value: {sspd} ")
ser.write(f'INDX={indx_dir}\n'.encode())

if not wait_indexed(ser, timeout=20.0):
    # try opposite once if the first pass didn't catch index
    ser.write(b'SSPD=5000\n'); time.sleep(0.05)
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
pto2_now = get_int(ser, "PTO2")
if not wait_pos(ser, 0, pto2=pto2_now, timeout=12.0):
    # nudge and try once more if we were right on a soft limit edge
    ser.write(b'SSPD=20000\n'); time.sleep(0.05)  # 1.5 mm/s
    ser.write(b'SCAN=1\n'); time.sleep(0.3); ser.write(b'SCAN=0\n'); time.sleep(0.1)
    ser.write(b'DPOS=0\n')
    if not wait_pos(ser, 0, pto2=pto2_now, timeout=12.0):
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
ser.write(b'SSPD=5000\n'); time.sleep(0.05)   # 2 mm/s
ser.write(b'SCAN=1\n');   time.sleep(5.0)
ser.write(b'SCAN=0\n')

 # Try movement
print("Moving............")



def move_counts_and_report_mm(ser, target_counts, *, pto2, timeout, axis=None, send_wait_ms=100, use_wait_pos=True):
    """
    Moves to 'target_counts', waits, then prints DPOS/EPOS in counts and mm.
    Requires your existing wait_pos(ser, target_counts, pto2, timeout).
    """
    prefix = (axis.encode() + b":") if axis else b""
    def send(cmd_bytes):
        ser.write(prefix + cmd_bytes + b"\n")

    # Make sure replies come back line-based
    send(b"ECHO=1")
    ser.reset_input_buffer()

    # 1) Command the move
    send(f"DPOS={int(target_counts)}".encode())
    if send_wait_ms:
        send(f"WAIT={int(send_wait_ms)}".encode())

    ok = True
    if use_wait_pos:
        ok = wait_pos(ser, target_counts, pto2=pto2, timeout=timeout)

    # 2) Query EPOS and print
    send(b"EPOS=?")
    epos_counts = _read_tag_int(ser, b"EPOS", prefix=prefix, window=1.0)

    dpos_mm = counts_to_mm(target_counts)
    if epos_counts is None:
        print(f"DPOS: {target_counts} cnt  ({dpos_mm:.6f} mm)")
        print("EPOS: <no reply>")
    else:
        if(target_counts > hlim) or (target_counts < llim):
            print(f"⚠️ Target position is not given within the limits")
        else:
            epos_mm = counts_to_mm(epos_counts)
            print(f"DPOS: {target_counts} cnt  ({dpos_mm:.6f} mm)")
            print(f"EPOS: {epos_counts} cnt  ({epos_mm:.6f} mm)")
            print(f"✅ Reached position {dpos_mm:.6f} mm with EPOS: {   epos_mm:.6f} mm")
    return {
        "ok": ok,
        "dpos_counts": target_counts, "dpos_mm": dpos_mm,
        "epos_counts": epos_counts, "epos_mm": (counts_to_mm(epos_counts) if epos_counts is not None else None),
    }

def move_mm_and_report(ser, target_mm, *, pto2, timeout, axis=None, **kw):
    """Same as above but you specify the target in mm."""
    counts = mm_to_counts(target_mm)
    return move_counts_and_report_mm(ser, counts, pto2=pto2, timeout=timeout, axis=axis, **kw)

#Usage
move_counts_and_report_mm(ser,  15500, pto2=pto2_now, timeout=12.0)   # ~19.375 mm
move_counts_and_report_mm(ser,      0, pto2=pto2_now, timeout=12.0)   # 0 mm
# # move_mm_and_report(ser, 25,pto2=pto2_now, timeout=12.0)               
# # move_mm_and_report(ser, -25,pto2=pto2_now, timeout=12.0)
move_mm_and_report(ser, - 95,pto2=pto2_now, timeout=12.0) 


#to Check if the bit 14th goes high once we reach at the left end during scan
def poll_stat_bits(ser, window=1.0):
    import time
    t0 = time.time()
    while time.time() - t0 < window:
        ser.write(b'STAT=?\n')
        line = ser.readline().strip()
        if line.startswith(b'STAT='):
            val = int(line.split(b'=')[1])
            left_end = bool(val & (1 << 14))
            right_end = bool(val & (1 << 15))
            # print(f"STAT={val}  LeftEnd={left_end}  RightEnd={right_end}")
        time.sleep(0.05)

# push into limit for a moment, then stop and poll
# ser.write(b'SSPD=20000\n')   # modest speed
# ser.write(b'SCAN=-1\n')
# time.sleep(0.6)             # short push toward the left
# ser.write(b'SCAN=0\n')
# poll_stat_bits(ser, window=0.6)
# print("STAT:", stat(ser), bits(stat(ser))) 

'''
ser.write(b'DPOS=15500\n') #1 count = 0.00125 mm . Multiply and get the EPOS and DPOS In MM
time.sleep(3)
ser.write(b'WAIT=100\n')
if  wait_pos(ser, 15500, pto2=pto2_now, timeout=12.0):
    # print("position reached")
    ser.write(b'EPOS=?\n')
    time.sleep(0.5)
    print("DPOS=15500")
    print(f"Position: {ser.read(100)}")

ser.write(b'DPOS=0\n') #1 count = 0.00125 mm . Multiply and get the EPOS and DPOS In MM
time.sleep(3)
ser.write(b'WAIT=100\n')
if  wait_pos(ser, 0, pto2=pto2_now, timeout=12.0):
    # print("position reached")
    ser.write(b'EPOS=?\n')
    time.sleep(0.5)
    print("DPOS = 0")
    print(f"Position: {ser.read(100)}")

ser.write(b'DPOS=-25500\n') #1 count = 0.00125 mm . Multiply and get the EPOS and DPOS In MM
time.sleep(3.0)
ser.write(b'WAIT=100\n')
if  wait_pos(ser, -25500, pto2=pto2_now, timeout=15.0):
    # print("position reached")
    ser.write(b'EPOS=?\n')
    time.sleep(0.5)
    print("DPOS=-25500")
    print(f"Position: {ser.read(100)}")
    '''