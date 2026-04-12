#!/usr/bin/env python3
"""
PSCM RAM dump via ELM327 on COM3.
Close FORScan before running!

Usage: python pscm_dump.py
"""
import serial
import time
import sys
import struct

PORT = 'COM3'
BAUD = 115200
PSCM_ADDR = '730'  # PSCM CAN ID (request)

def elm_cmd(s, cmd, timeout=2):
    """Send AT command, return response."""
    s.flushInput()
    s.write((cmd + '\r').encode())
    time.sleep(0.1)
    resp = b''
    end = time.time() + timeout
    while time.time() < end:
        chunk = s.read(s.in_waiting or 1)
        resp += chunk
        if b'>' in resp:
            break
        if not chunk:
            time.sleep(0.05)
    return resp.decode('ascii', errors='replace').strip().replace('\r\r', '\r')


def elm_init(s):
    """Initialize ELM327 for CAN communication with PSCM."""
    print("Initializing ELM327...")

    r = elm_cmd(s, 'ATZ', 3)
    print(f'  ATZ: {r}')

    r = elm_cmd(s, 'ATE0')  # echo off
    r = elm_cmd(s, 'ATL0')  # linefeeds off
    r = elm_cmd(s, 'ATS0')  # spaces off (for easier parsing)

    # Set protocol to ISO 15765-4 CAN (11-bit, 500kbps)
    r = elm_cmd(s, 'ATSP6')
    print(f'  Protocol: {r}')

    # Set header to PSCM address
    r = elm_cmd(s, f'ATSH{PSCM_ADDR}')
    print(f'  Header: {r}')

    # Set CAN receive filter for PSCM response (0x738)
    r = elm_cmd(s, 'ATCRA738')
    print(f'  Filter: {r}')

    # Flow control
    r = elm_cmd(s, 'ATFCSH730')  # FC header
    r = elm_cmd(s, 'ATFCSD300000')  # FC data (continue, no delay)
    r = elm_cmd(s, 'ATFCSM1')  # FC mode = user defined

    print("  Init complete")
    return True


def uds_request(s, data_hex, timeout=5):
    """Send UDS request, return response bytes."""
    resp = elm_cmd(s, data_hex, timeout)

    # Parse hex response - remove whitespace and prompts
    lines = resp.replace('>', '').strip().split('\r')
    hex_data = ''
    for line in lines:
        line = line.strip()
        if line and all(c in '0123456789ABCDEFabcdef' for c in line):
            hex_data += line

    if hex_data:
        try:
            return bytes.fromhex(hex_data)
        except:
            pass

    return resp.encode()


def read_memory(s, addr, size):
    """UDS ReadMemoryByAddress (0x23)."""
    # Service 0x23, addressAndLengthFormatId 0x44 (4-byte addr, 4-byte size)
    cmd = f'2344{addr:08X}{size:08X}'
    return uds_request(s, cmd)


def extended_session(s):
    """Enter extended diagnostic session."""
    resp = uds_request(s, '1003')
    print(f'  Extended session: {resp.hex() if isinstance(resp, bytes) else resp}')
    return resp


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=== PSCM RAM Dump ===")
    print(f"Port: {PORT} @ {BAUD}")
    print()

    try:
        s = serial.Serial(PORT, BAUD, timeout=2)
    except serial.SerialException as e:
        print(f"ERROR: {e}")
        print("Make sure FORScan is CLOSED!")
        return

    if not elm_init(s):
        s.close()
        return

    print()
    print("--- Entering extended session ---")
    extended_session(s)
    time.sleep(0.5)

    # Quick test reads
    regions = [
        ("Timer table (cal+0x06B0)", 0x00FD06B0, 0x14),
        ("LCA cal (cal+0x346C)",     0x00FD346C, 0x10),
        ("APA speed (cal+0x02C4)",   0x00FD02C4, 0x20),
        ("TKP_INFO",                 0x01002028, 0x30),
        ("Removed code check",       0x010E1000, 0x10),
        ("EP area start",            0x40010100, 0x40),
        ("EP+0x6A (signal input)",   0x4001016A, 0x10),
    ]

    print()
    print("--- Reading memory ---")

    for name, addr, size in regions:
        print(f'\n{name} @ 0x{addr:08X} ({size} bytes):')
        resp = read_memory(s, addr, size)

        if isinstance(resp, bytes) and len(resp) > 1:
            if resp[0] == 0x63:
                # Success - data follows service ID
                data = resp[1:]
                # Print hex dump
                for i in range(0, len(data), 16):
                    chunk = data[i:i+16]
                    hex_str = ' '.join(f'{b:02X}' for b in chunk)
                    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                    print(f'  {addr+i:08X}: {hex_str:<48s} {ascii_str}')

                # Save raw data
                with open(f'C:/Users/Zorro/Desktop/fwproject/firmware/ram_dump/{name.replace(" ","_").replace("(","").replace(")","")}.bin', 'wb') as f:
                    f.write(data)
            elif resp[0] == 0x7F:
                nrc = resp[2] if len(resp) > 2 else 0
                nrc_names = {0x22:'conditionsNotCorrect', 0x31:'requestOutOfRange',
                            0x33:'securityAccessDenied', 0x14:'responseTooLong'}
                print(f'  ERROR: NRC=0x{nrc:02X} ({nrc_names.get(nrc, "unknown")})')
            else:
                print(f'  Response: {resp.hex()}')
        else:
            print(f'  Raw: {resp}')

    # Full EP area dump if quick test works
    print("\n--- Full EP area dump ---")
    import os
    os.makedirs('C:/Users/Zorro/Desktop/fwproject/firmware/ram_dump', exist_ok=True)

    full_dump = bytearray()
    for offset in range(0, 0x400, 0x40):
        addr = 0x40010100 + offset
        resp = read_memory(s, addr, 0x40)
        if isinstance(resp, bytes) and len(resp) > 1 and resp[0] == 0x63:
            full_dump.extend(resp[1:])
            sys.stdout.write('.')
            sys.stdout.flush()
        else:
            print(f'\n  Failed at 0x{addr:08X}')
            break

    if full_dump:
        with open('C:/Users/Zorro/Desktop/fwproject/firmware/ram_dump/ep_area_full.bin', 'wb') as f:
            f.write(full_dump)
        print(f'\n  Saved {len(full_dump)} bytes to ep_area_full.bin')

    s.close()
    print("\nDone!")


if __name__ == '__main__':
    main()
