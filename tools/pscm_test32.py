"""PSCM CAN test using 32-bit Ford RLink DLL. Run with 32-bit Python."""
import ctypes, struct, time, sys

DLL = r"C:\Program Files\TOPDON\J2534\FORD\RLink-FDRS.dll"

# J2534 constants
ISO15765 = 6
CAN = 5
FLOW_CONTROL_FILTER = 3
PASS_FILTER = 1

class PASSTHRU_MSG(ctypes.Structure):
    _fields_ = [
        ("ProtocolID", ctypes.c_ulong),
        ("RxStatus", ctypes.c_ulong),
        ("TxFlags", ctypes.c_ulong),
        ("Timestamp", ctypes.c_ulong),
        ("DataSize", ctypes.c_ulong),
        ("ExtraDataIndex", ctypes.c_ulong),
        ("Data", ctypes.c_ubyte * 4128),
    ]

def make_msg(proto, data):
    m = PASSTHRU_MSG()
    m.ProtocolID = proto
    m.DataSize = len(data)
    for i, b in enumerate(data):
        m.Data[i] = b
    return m

dll = ctypes.WinDLL(DLL)
dev = ctypes.c_ulong(0)
ret = dll.PassThruOpen(None, ctypes.byref(dev))
print(f"Open: ret={ret} dev={dev.value}")

ch = ctypes.c_ulong(0)
ret = dll.PassThruConnect(dev, CAN, 0, 500000, ctypes.byref(ch))
print(f"CAN Connect: ret={ret} ch={ch.value}")

# Pass filter to receive all
mask = make_msg(CAN, struct.pack('>I', 0x00000000))
pattern = make_msg(CAN, struct.pack('>I', 0x00000000))
filt = ctypes.c_ulong(0)
ret = dll.PassThruStartMsgFilter(ch, PASS_FILTER, ctypes.byref(mask), ctypes.byref(pattern), None, ctypes.byref(filt))
print(f"Filter: ret={ret} filt={filt.value}")

# Listen
print("\nListening CAN 500k for 5 seconds...")
seen = {}
end = time.time() + 5
while time.time() < end:
    msg = PASSTHRU_MSG()
    num = ctypes.c_ulong(1)
    ret = dll.PassThruReadMsgs(ch, ctypes.byref(msg), ctypes.byref(num), 100)
    if ret == 0 and num.value > 0:
        cid = struct.unpack_from('>I', bytes(msg.Data[:4]))[0]
        data = bytes(msg.Data[4:msg.DataSize])
        if cid not in seen:
            seen[cid] = data
            known = {0x082:'EPAS_INFO', 0x07E:'StePinion', 0x3CC:'LKA_Stat',
                     0x415:'BrkSpeed', 0x213:'DesTorq', 0x091:'Yaw',
                     0x730:'PSCM_Diag', 0x738:'PSCM_Resp'}
            name = known.get(cid, '')
            print(f"  0x{cid:03X} {name:12s} {data[:8].hex()}")

print(f"\nTotal: {len(seen)} unique CAN IDs")

# Now try ISO15765 to talk to PSCM
dll.PassThruDisconnect(ch)

ch2 = ctypes.c_ulong(0)
ret = dll.PassThruConnect(dev, ISO15765, 0, 500000, ctypes.byref(ch2))
print(f"\nISO15765 Connect: ret={ret} ch={ch2.value}")

if ret == 0:
    # Flow control filter for PSCM
    mask = make_msg(ISO15765, struct.pack('>I', 0xFFFFFFFF))
    pattern = make_msg(ISO15765, struct.pack('>I', 0x738))
    flow = make_msg(ISO15765, struct.pack('>I', 0x730))
    filt2 = ctypes.c_ulong(0)
    ret = dll.PassThruStartMsgFilter(ch2, FLOW_CONTROL_FILTER,
        ctypes.byref(mask), ctypes.byref(pattern), ctypes.byref(flow), ctypes.byref(filt2))
    print(f"PSCM Filter: ret={ret}")

    def uds(data):
        msg = make_msg(ISO15765, struct.pack('>I', 0x730) + data)
        num = ctypes.c_ulong(1)
        ret = dll.PassThruWriteMsgs(ch2, ctypes.byref(msg), ctypes.byref(num), 2000)
        if ret != 0: return None
        time.sleep(0.3)
        resp = PASSTHRU_MSG()
        rnum = ctypes.c_ulong(1)
        ret = dll.PassThruReadMsgs(ch2, ctypes.byref(resp), ctypes.byref(rnum), 2000)
        if ret == 0 and rnum.value > 0:
            return bytes(resp.Data[4:resp.DataSize])
        return None

    # Tester Present
    r = uds(b'\x3E\x00')
    print(f"Tester Present: {r.hex() if r else 'NO RESPONSE'}")

    # Extended Session
    r = uds(b'\x10\x03')
    print(f"Extended Session: {r.hex() if r else 'NO RESPONSE'}")

    # Read Strategy PN
    r = uds(struct.pack('>BH', 0x22, 0xF188))
    if r and r[0] == 0x62:
        print(f"Strategy: {r[3:].decode('ascii', errors='replace')}")

    # Read Cal PN
    r = uds(struct.pack('>BH', 0x22, 0xF10A))
    if r and r[0] == 0x62:
        print(f"Cal: {r[3:].decode('ascii', errors='replace')}")

    # READ TIMER TABLE
    print()
    r = uds(b'\x23\x44' + struct.pack('>II', 0x00FD06B0, 0x14))
    if r and r[0] == 0x63:
        d = r[1:]
        print("TIMER TABLE (cal+0x06B0):")
        for i in range(0, min(len(d), 20), 2):
            v = struct.unpack_from('>H', d, i)[0]
            print(f"  +0x{0x06B0+i:04X}: {v:5d} ({v*10}ms)")
    elif r:
        print(f"Timer error: {r.hex()}")
    else:
        print("Timer: no response")

    # Read APA speed table
    r = uds(b'\x23\x44' + struct.pack('>II', 0x00FD02C4, 0x20))
    if r and r[0] == 0x63:
        d = r[1:]
        print("\nAPA SPEED TABLE (cal+0x02C4):")
        for i in range(0, min(len(d), 32), 4):
            v = struct.unpack_from('>f', d, i)[0]
            print(f"  +0x{0x02C4+i:04X}: {v:.2f} kph")
    elif r:
        print(f"APA error: {r.hex()}")

    dll.PassThruDisconnect(ch2)

dll.PassThruClose(dev)
print("\nDone!")
