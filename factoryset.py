import time, re, serial

ser = serial.Serial('COM6', 9600, timeout=1.0, write_timeout=1.0)
time.sleep(0.2)

def nl_query(cmd: bytes, wait=0.06):
    # send a command terminated with \n and read one LF-terminated line
    ser.reset_input_buffer()
    ser.write(cmd + b'\n'); ser.flush()
    time.sleep(wait)
    return ser.read_until(b'\n', 512)

def read_tag_nl(tag: str, tries=8):
    pat = re.compile(rf'(?:[A-Z]:)?{re.escape(tag)}=([^\r\n]+)')
    last = b''
    for _ in range(tries):
        data = nl_query(tag.encode() + b'=?')
        last = data
        m = pat.search(data.decode(errors='ignore'))
        if m:
            val = m.group(1).strip()
            return int(val) if re.fullmatch(r'-?\d+', val) else val
        time.sleep(0.05)
    return f"<no reply: {last!r}>"

def factory_snapshot():
    # 1) Reset to factory, give it time to reboot
    ser.reset_input_buffer(); ser.reset_output_buffer()
    ser.write(b'FACT\n'); ser.flush()
    time.sleep(2.0)                     # many firmwares need ~1–2s after FACT

    # 2) (Optional but helps) reopen to clear any stale device buffers
    try:
        ser.close(); time.sleep(0.3); ser.open()
    except Exception:
        pass
    ser.reset_input_buffer(); ser.reset_output_buffer()

    # 3) Wake + stop streaming so replies aren’t garbled
    ser.write(b'\n'); time.sleep(0.05)   # wake poke
    ser.write(b'INFO=0\n'); time.sleep(0.1)
    ser.write(b'POLI=97\n'); time.sleep(0.1)

    # 4) Read everything with LF only
    tags = ["SOFT","SRNO","FILE","STAT","EPOS","LLIM","HLIM","FREQ","FRQ2",
            "ENCD","ENCO","PTOL","PTO2","SSPD","MSPD","ISPD","ACCE","DECE",
            "VOLT","AMPL","INFO","POLI"]
    snap = {t: read_tag_nl(t) for t in tags}
    w = max(len(k) for k in snap)
    print("\n=== FACTORY SNAPSHOT ===")
    for k in tags:
        print(f"{k.ljust(w)} : {snap[k]}")

factory_snapshot()
