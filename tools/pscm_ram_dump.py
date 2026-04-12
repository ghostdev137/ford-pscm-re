#!/usr/bin/env python3
"""
PSCM RAM dump via UDS ReadMemoryByAddress (service 0x23).

Generates FORScan-compatible ELM327/J2534 commands to read PSCM memory.

Usage: Run these commands in FORScan's "Run Service" or raw command mode,
       or use a CAN tool to send them directly to PSCM (address 0x730).

UDS ReadMemoryByAddress format:
  Request:  23 <addrLenFormat> <address> <size>
  Response: 63 <data...>

addrLenFormat = 0x44 means 4-byte address + 4-byte size
"""

import struct

# PSCM CAN addresses
PSCM_RX = 0x730   # Request to PSCM
PSCM_TX = 0x738   # Response from PSCM

# Memory regions to dump
REGIONS = [
    # RAM regions with BSW state / signal buffers
    ("EP_area",      0x40010100, 0x400),    # EP-relative area (BSW init flags)
    ("EP_extended",  0x40010500, 0x400),    # Extended EP area
    ("Signal_buf_1", 0x40014490, 0x400),    # ROM->RAM copy start (AUTOSAR signals)
    ("Signal_buf_2", 0x40018000, 0x400),    # Mid signal buffer
    ("Signal_buf_3", 0x4001C000, 0x400),    # Upper signal buffer
    ("CAN_buf",      0x4001CE00, 0x100),    # Near ROM->RAM end

    # Calibration (ROM - verify our flash took effect)
    ("Cal_timer",    0x00FD06B0, 0x20),     # Timer table (should be zeroed)
    ("Cal_LCA_1",    0x00FD33DD, 0x40),     # LCA data block 1 start
    ("Cal_LCA_2",    0x00FD3AD1, 0x40),     # LCA data block 2 start
    ("Cal_APA",      0x00FD02C0, 0x60),     # APA speed table

    # CAN controller
    ("RSCAN_MB",     0xFFD00100, 0x200),    # RS-CAN mailboxes

    # Code area (verify strategy version)
    ("TKP_header",   0x01002000, 0x80),     # TKP_INFO header
    ("Removed_code", 0x010E1000, 0x20),     # Removed area (zero on AM, code on AH)
]


def make_uds_read(addr, size):
    """Generate UDS ReadMemoryByAddress request."""
    # Service 0x23, addressAndLengthFormatId 0x44 (4+4)
    return bytes([0x23, 0x44]) + struct.pack('>I', addr) + struct.pack('>I', size)


def format_hex(data):
    return ' '.join(f'{b:02X}' for b in data)


def main():
    print("=" * 60)
    print("PSCM RAM Dump Commands for FORScan")
    print("=" * 60)
    print()
    print("STEP 1: Open FORScan, connect to vehicle")
    print("STEP 2: Go to 'Service Functions' or raw command mode")
    print("STEP 3: Select PSCM module (0x730)")
    print("STEP 4: First send extended diagnostic session:")
    print(f"   Command: 10 03")
    print()
    print("STEP 5: Try security access if needed:")
    print(f"   Command: 27 01  (request seed)")
    print(f"   Then:    27 02 <key>  (send key based on seed)")
    print()
    print("STEP 6: Send these ReadMemoryByAddress commands:")
    print()

    for name, addr, size in REGIONS:
        # UDS can only read ~256 bytes per request on CAN (limited by transport layer)
        # Split into 64-byte chunks for safety
        chunk = min(size, 64)
        for offset in range(0, size, chunk):
            read_size = min(chunk, size - offset)
            cmd = make_uds_read(addr + offset, read_size)
            cmd_hex = format_hex(cmd)
            print(f"  # {name} @ 0x{addr+offset:08X} ({read_size} bytes)")
            print(f"  {cmd_hex}")
            print()

    print("=" * 60)
    print("Expected responses:")
    print("  63 XX XX XX ... = success (data follows)")
    print("  7F 23 31 = requestOutOfRange (address not readable)")
    print("  7F 23 33 = securityAccessDenied (need auth)")
    print("  7F 23 22 = conditionsNotCorrect (wrong session)")
    print("=" * 60)
    print()

    # Also generate a compact version for quick testing
    print("QUICK TEST (just verify cal was flashed correctly):")
    print()
    print("  # Extended session")
    print("  10 03")
    print()
    print("  # Read timer table (should be all zeros after our patch)")
    cmd = make_uds_read(0x00FD06B0, 0x14)
    print(f"  # Timer table cal+0x06B0 (20 bytes)")
    print(f"  {format_hex(cmd)}")
    print()
    print("  # Read LCA data (should NOT be 0xFF after our patch)")
    cmd = make_uds_read(0x00FD346C, 0x10)
    print(f"  # LCA GP-offset cal+0x346C (16 bytes)")
    print(f"  {format_hex(cmd)}")
    print()
    print("  # Read TKP header (identifies strategy version)")
    cmd = make_uds_read(0x01002028, 0x30)
    print(f"  # TKP_INFO string")
    print(f"  {format_hex(cmd)}")


if __name__ == '__main__':
    main()
