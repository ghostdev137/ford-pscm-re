#!/usr/bin/env python3
"""
PSCM CAN test via VCM-II J2534.
Close FORScan before running!
"""
import struct, time, sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'reference', 'PyJ2534'))
import PyJ2534
from PyJ2534.define import *

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=== PSCM CAN Test via VCM-II ===\n")

    # Enumerate interfaces
    ifaces = PyJ2534.get_interfaces()
    print(f"J2534 interfaces: {ifaces}")

    if not ifaces:
        print("No J2534 interfaces found!")
        return

    # Use the 64-to-32 bridge DLL (Python is 64-bit, VCM-II DLL is 32-bit)
    bridge_path = r"C:\Program Files\Ford Motor Company\J2534_64_32_Bridge\J2534CLT64.dll"
    if os.path.exists(bridge_path):
        iface_path = bridge_path
        iface_name = "J2534 64-to-32 Bridge"
    else:
        iface_path = list(ifaces.values())[0]
        iface_name = list(ifaces.keys())[0]
    print(f"Using: {iface_name}")
    print(f"DLL: {iface_path}")

    j = PyJ2534.load_interface(iface_path)

    dev_id = j.PassThruOpen()
    print(f"Device opened: {dev_id.value}")

    ch_id = j.PassThruConnect(dev_id, ProtocolID.ISO15765, 0, 500000)
    print(f"Connected ISO15765: channel={ch_id.value}")

    # Flow control filter for PSCM (0x730 -> 0x738)
    mask = PASSTHRU_MSG(ProtocolID.ISO15765)
    mask.DataSize = 4
    struct.pack_into('>I', (ctypes.c_ubyte * 4096).from_buffer(mask.Data), 0, 0xFFFFFFFF)

    pattern = PASSTHRU_MSG(ProtocolID.ISO15765)
    pattern.DataSize = 4
    struct.pack_into('>I', (ctypes.c_ubyte * 4096).from_buffer(pattern.Data), 0, 0x738)

    flow = PASSTHRU_MSG(ProtocolID.ISO15765)
    flow.DataSize = 4
    struct.pack_into('>I', (ctypes.c_ubyte * 4096).from_buffer(flow.Data), 0, 0x730)

    filt_id = j.PassThruStartMsgFilter(ch_id, FilterType.FLOW_CONTROL, mask, pattern, flow)
    print(f"Filter set: {filt_id.value}")

    def send_uds(data: bytes, timeout=2000):
        msg = PASSTHRU_MSG(ProtocolID.ISO15765)
        payload = struct.pack('>I', 0x730) + data
        msg.DataSize = len(payload)
        for i, b in enumerate(payload):
            msg.Data[i] = b

        j.PassThruWriteMsgs(ch_id, [msg], timeout)
        time.sleep(0.2)

        try:
            responses = j.PassThruReadMsgs(ch_id, 1, timeout)
            if responses:
                resp = responses[0]
                return bytes(resp.Data[4:resp.DataSize])
        except:
            pass
        return None

    # Test 1: Tester Present
    print("\n--- Tester Present ---")
    resp = send_uds(b'\x3E\x00')
    print(f"  {resp.hex() if resp else 'NO RESPONSE'}")

    # Test 2: Extended Session
    print("\n--- Extended Session ---")
    resp = send_uds(b'\x10\x03')
    print(f"  {resp.hex() if resp else 'NO RESPONSE'}")

    # Test 3: Read DIDs
    print("\n--- Read DIDs ---")
    for did, name in [(0xF188, 'Strategy'), (0xF10A, 'Cal'), (0xF195, 'System')]:
        resp = send_uds(struct.pack('>BH', 0x22, did))
        if resp and resp[0] == 0x62:
            print(f"  {name}: {resp[3:].decode('ascii', errors='replace')}")
        elif resp:
            print(f"  {name}: {resp.hex()}")
        else:
            print(f"  {name}: no response")

    # Test 4: Read Timer Table
    print("\n--- Timer Table (cal+0x06B0) ---")
    resp = send_uds(b'\x23\x44' + struct.pack('>II', 0x00FD06B0, 0x14))
    if resp and resp[0] == 0x63:
        data = resp[1:]
        for i in range(0, min(len(data), 20), 2):
            v = struct.unpack_from('>H', data, i)[0]
            print(f"  +0x{0x06B0+i:04X}: {v:5d} ({v*10}ms)")
    elif resp:
        print(f"  Error: {resp.hex()}")
    else:
        print("  No response")

    # Test 5: Read LCA cal
    print("\n--- LCA Cal Check (cal+0x346C) ---")
    resp = send_uds(b'\x23\x44' + struct.pack('>II', 0x00FD346C, 0x10))
    if resp and resp[0] == 0x63:
        data = resp[1:]
        is_ff = all(b == 0xFF for b in data)
        print(f"  Data: {data.hex()}")
        print(f"  {'ALL 0xFF — NO LCA DATA' if is_ff else 'HAS DATA — LCA POPULATED'}")
    elif resp:
        print(f"  Error: {resp.hex()}")

    # Test 6: Read EP area
    print("\n--- EP Area (BSW state) ---")
    resp = send_uds(b'\x23\x44' + struct.pack('>II', 0x40010100, 0x20))
    if resp and resp[0] == 0x63:
        data = resp[1:]
        print(f"  {data.hex()}")
    elif resp:
        print(f"  Error: {resp.hex()}")

    j.PassThruDisconnect(ch_id)
    j.PassThruClose(dev_id)
    print("\nDone!")

import ctypes
if __name__ == '__main__':
    main()
