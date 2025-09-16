import re, time
import serial.tools.list_ports

# --- I/O helpers -------------------------------------------------------------
EOL = b'\r\n'                     # safest: send CRLF; device will reply with \n or \r\n


def _query_bytes(cmd: bytes, wait=0.03):
    ser.reset_input_buffer()               # avoid parsing stale data
    ser.write(cmd + EOL)
    time.sleep(wait)
    # prefer LF-terminated replies; fall back to CR-only if needed
    data = ser.read_until(b'\n', 256) or ser.read_until(b'\r', 256)
    return data

def read_tag(tag: str, tries=6):
    pat = re.compile(rf'(?:[A-Z]:)?{re.escape(tag)}=([^\r\n]+)')
    last = b''
    for _ in range(tries):
        data = _query_bytes(tag.encode() + b'=?')
        last = data
        m = pat.search(data.decode(errors='ignore'))
        if m:
            val = m.group(1).strip()
            # return int when numeric, else raw string
            return int(val) if re.fullmatch(r'-?\d+', val) else val
        time.sleep(0.05)
    raise RuntimeError(f"No reply for {tag}=? (last={last!r})")

def write_tag(tag: str, value, axis: str | None = None):
    # add axis prefix for per-axis settings when provided
    prefix = (axis + ":") if axis else ""
    payload = f"{prefix}{tag}={value}".encode()
    _ = _query_bytes(payload)              # ignore echo/ok; you can print if you want

# --- bulk read / write -------------------------------------------------------
# what to read right after LOAD (tweak as you like)
READBACK_TAGS = [
    "SOFT","SRNO","STAT","EPOS","LLIM","HLIM","FREQ","FRQ2","ENCD","ENCO",
    "PTOL","PTO2","SSPD","MSPD","ISPD","ACCE","DECE","VOLT","AMPL","INFO","POLI",
    "HFRQ","LFRQ","PROP","PRO2","MPRO","INTF","MASS","MMAS","ZON1","ZON2",
    "ACCE","DECE","ILIM","ELIM","SLIM","ACTD","TOUT","TOU2","TOU3","ENBR","ENBL",
    "INDA","DTIM","UART","PHAC","PHAS","DUCO","MIMP","MAMP","AMPL","DUTY","OFSA",
    "OFSB","SQEZ","COMP","DLAY","DTIM","FILE","FILA","FILG","FILP","PLIM","DLAY"
]

# settings you want to enforce AFTER LOAD (example; edit values for your setup)
DESIRED = {
    # global
    "INFO": 0, "POLI": 97, "FREQ": 87000, "FRQ2": 86000, "ENCO": 0, "ENCD": 0,
    # per-axis (use axis prefix below)
    "ENBL": 1, "LLIM": -200000, "HLIM": 200000, "PTOL": 400, "PTO2": 400, "SSPD": 2000
}

# per-axis keys (will be sent as 'X:TAG=...')
PER_AXIS = {"ENBL","LLIM","HLIM","PTOL","PTO2","SSPD","MSPD","ISPD","ACCE","DECE"}

def read_many(tags):
    out = {}
    for t in tags:
        try:
            out[t] = read_tag(t)
        except Exception as e:
            out[t] = f"<no reply: {e}>"
    return out

def apply_settings(desired: dict, axis_letter: str | None = "X"):
    changes = {}
    # read current first
    current = {}
    for k in desired.keys():
        try:
            current[k] = read_tag(k)
        except Exception:
            current[k] = None
    # write only differences
    for k, v in desired.items():
        is_axis = k in PER_AXIS
        if current.get(k) != v:
            write_tag(k, v, axis_letter if is_axis else None)
            changes[k] = (current.get(k), v)
            time.sleep(0.02)  # tiny dwell between writes
    return changes

def print_kv_table(d, title):
    print(f"\n{title}")
    width = max(len(k) for k in d.keys()) if d else 0
    for k in d:
        print(f"  {k.ljust(width)} : {d[k]}")
    print()

# --- EXAMPLE USAGE -----------------------------------------------------------
ser = serial.Serial('COM6', 9600, timeout=0.5)
time.sleep(0.3)

ser.reset_input_buffer(); ser.reset_output_buffer()

# 0) Clean slate, closed-loop stage
ser.write(b'RSET=0\n'); time.sleep(0.3)
# ser.write(b'XLA3=1250\n'); time.sleep(0.1)
ser.write(b'LOAD=0\n');   time.sleep(0.2)
time.sleep(0.1)

ser.reset_input_buffer(); ser.reset_output_buffer()
ser.timeout = 1.0; ser.write_timeout = 1.0

# 2) Read existing settings (array/loop)
old = read_many(READBACK_TAGS)
print_kv_table(old, "Current settings (after LOAD)")

# 3) Apply your desired settings (idempotent: only writes diffs)
#changes = apply_settings(DESIRED, axis_letter="X")
#print_kv_table({k: f"{a} -> {b}" for k,(a,b) in changes.items()}, "Applied changes")

# 4) Verify
#new = read_many(READBACK_TAGS)
#print_kv_table(new, "Settings after apply")
