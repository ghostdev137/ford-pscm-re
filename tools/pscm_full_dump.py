"""
Full PSCM firmware dumper.

Walks UDS 0x23 ReadMemoryByAddress over arbitrary address ranges and writes
the result to a binary file. Designed for building complete memory images
for emulator loading (Athrill) and for pre-flash verification.

Usage (from 32-bit Python 3.12 on Windows, with TOPDON RLink or VCM-II J2534):

    python tools/pscm_full_dump.py \
        --dll "C:\\Program Files\\TOPDON\\J2534\\FORD\\RLink-FDRS.dll" \
        --start 0x00FD0000 --length 0x10000 --chunk 64 \
        --output analysis/transit/cal_live_dump.bin

Typical regions to dump:

    Transit 2025 PSCM (V850E2M):
      --start 0x00000000 --length 0x1000           boot ROM (if readable)
      --start 0x00F00000 --length 0xD0000          strategy (block0)
      --start 0x00FD0000 --length 0xFFF0           calibration
      --start 0x40000000 --length 0x20000          RAM (live state — useful!)

    F-150 2021 Lariat PSCM (RH850):
      --start 0x00000000 --length 0x1000           boot ROM
      --start 0x10040000 --length 0x17FC00         strategy
      --start 0x101C0000 --length 0x10000          supplementary
      --start 0x101D0000 --length 0x2FC00          calibration
      --start 0xFEBE0000 --length 0x2284           SBL staging
      --start 0xFEC00000 --length 0x20000          RAM (live state)

After flashing modifications, dumping RAM + the flash regions lets the
Athrill emulator boot from a snapshot of the *actual vehicle state*
rather than a cold-start guess.

Requirements:
- 32-bit Python (Ford J2534 DLLs are 32-bit)
- TOPDON RLink Platform middleware running (for the RLink-FDRS.dll)
- OR genuine Ford VCM-II J2534 stack + FORScan Extended (license may
  gate access to security-required read regions)
- Ignition ON, accessory mode (engine off preferred)

CAUTION: This needs an Extended Diagnostic session (0x10 0x03) and, for
some regions, SecurityAccess (0x27). Without 0x27 the PSCM will return
NRC 0x33 (securityAccessDenied) on protected address ranges. The boot
ROM and certain flash regions are typically security-locked.
"""
import argparse, ctypes, struct, sys, time, os


# J2534 Protocol IDs
J1850VPW = 1
J1850PWM = 2
ISO9141  = 3
ISO14230 = 4
CAN      = 5
ISO15765 = 6

# Filter types
PASS_FILTER         = 1
BLOCK_FILTER        = 2
FLOW_CONTROL_FILTER = 3

# Connect flags
ISO15765_FRAME_PAD  = 0x00000040


class PASSTHRU_MSG(ctypes.Structure):
    _fields_ = [
        ("ProtocolID",     ctypes.c_ulong),
        ("RxStatus",       ctypes.c_ulong),
        ("TxFlags",        ctypes.c_ulong),
        ("Timestamp",      ctypes.c_ulong),
        ("DataSize",       ctypes.c_ulong),
        ("ExtraDataIndex", ctypes.c_ulong),
        ("Data",           ctypes.c_ubyte * 4128),
    ]


def make_msg(proto, data, tx_flags=ISO15765_FRAME_PAD):
    m = PASSTHRU_MSG()
    m.ProtocolID = proto
    m.TxFlags = tx_flags
    m.DataSize = len(data)
    for i, b in enumerate(data):
        m.Data[i] = b
    return m


class PSCMClient:
    def __init__(self, dll_path, ecu_req=0x730, ecu_resp=0x738, baud=500000):
        self.dll = ctypes.WinDLL(dll_path)
        self.dev = ctypes.c_ulong(0)
        self.ch = ctypes.c_ulong(0)
        self.ecu_req = ecu_req
        self.ecu_resp = ecu_resp
        self.baud = baud

    def open(self):
        ret = self.dll.PassThruOpen(None, ctypes.byref(self.dev))
        if ret != 0:
            raise RuntimeError(f"PassThruOpen failed: {ret}")
        print(f"[j2534] opened device {self.dev.value}")

    def connect(self):
        ret = self.dll.PassThruConnect(
            self.dev, ISO15765, ISO15765_FRAME_PAD, self.baud, ctypes.byref(self.ch)
        )
        if ret != 0:
            raise RuntimeError(f"PassThruConnect failed: {ret}")
        mask    = make_msg(ISO15765, struct.pack('>I', 0xFFFFFFFF), tx_flags=0)
        pattern = make_msg(ISO15765, struct.pack('>I', self.ecu_resp), tx_flags=0)
        flow    = make_msg(ISO15765, struct.pack('>I', self.ecu_req), tx_flags=0)
        filt = ctypes.c_ulong(0)
        ret = self.dll.PassThruStartMsgFilter(
            self.ch, FLOW_CONTROL_FILTER,
            ctypes.byref(mask), ctypes.byref(pattern),
            ctypes.byref(flow), ctypes.byref(filt))
        if ret != 0:
            raise RuntimeError(f"PassThruStartMsgFilter failed: {ret}")
        print(f"[j2534] connected ISO15765 on ch {self.ch.value}, filter {filt.value}")

    def uds(self, req_bytes, timeout_ms=1500):
        """Send a UDS request and collect the response. Returns response bytes (after SID echo)."""
        payload = struct.pack('>I', self.ecu_req) + req_bytes
        msg = make_msg(ISO15765, payload)
        num = ctypes.c_ulong(1)
        ret = self.dll.PassThruWriteMsgs(self.ch, ctypes.byref(msg), ctypes.byref(num), timeout_ms)
        if ret != 0:
            return None
        time.sleep(0.02)
        # collect responses until positive or negative
        deadline = time.time() + timeout_ms / 1000.0
        while time.time() < deadline:
            resp = PASSTHRU_MSG()
            n = ctypes.c_ulong(1)
            ret = self.dll.PassThruReadMsgs(self.ch, ctypes.byref(resp), ctypes.byref(n), 200)
            if ret == 0 and n.value > 0:
                payload = bytes(resp.Data[4:resp.DataSize])  # strip 4-byte CAN ID prefix
                if not payload:
                    continue
                # handle NRC (0x7F)
                if payload[0] == 0x7F:
                    nrc = payload[2] if len(payload) > 2 else 0
                    if nrc == 0x78:  # requestCorrectlyReceived-ResponsePending
                        deadline = time.time() + timeout_ms / 1000.0
                        continue
                    return payload  # return NRC so caller can decide
                return payload
        return None

    def session(self, session_type=0x03):
        """DiagnosticSessionControl. 0x03 = Extended Diagnostic."""
        return self.uds(bytes([0x10, session_type]))

    def tester_present(self):
        return self.uds(bytes([0x3E, 0x00]))

    def read_did(self, did):
        """Read Data by Identifier (0x22). Returns the data bytes after the 0x62 xx xx echo."""
        resp = self.uds(struct.pack('>BH', 0x22, did))
        if resp and resp[0] == 0x62 and len(resp) >= 3:
            return resp[3:]
        return None

    def read_memory(self, addr, length, addr_size=4, len_size=2):
        """
        UDS 0x23 ReadMemoryByAddress.
        Format byte: high nibble = length-of-length, low nibble = length-of-address.
        addr_size 4 + len_size 2 -> format 0x24
        """
        if addr_size not in (2, 3, 4) or len_size not in (1, 2, 3, 4):
            raise ValueError("invalid size combo")
        fmt = (len_size << 4) | addr_size
        req = bytes([0x23, fmt]) + addr.to_bytes(addr_size, 'big') + length.to_bytes(len_size, 'big')
        resp = self.uds(req, timeout_ms=3000)
        if resp is None:
            return None
        if resp[0] == 0x63:
            return resp[1:]
        # NRC
        nrc = resp[2] if len(resp) > 2 else 0xFF
        return {'nrc': nrc, 'raw': resp}

    def close(self):
        try: self.dll.PassThruDisconnect(self.ch)
        except Exception: pass
        try: self.dll.PassThruClose(self.dev)
        except Exception: pass


def dump_range(client, start, length, chunk, output_path, skip_errors=True):
    """Dump [start, start+length) in `chunk`-byte requests. Writes bytes as they come in."""
    written = 0
    gap_count = 0
    t0 = time.time()
    with open(output_path, 'wb') as f:
        addr = start
        end  = start + length
        while addr < end:
            this_len = min(chunk, end - addr)
            r = client.read_memory(addr, this_len)
            if isinstance(r, dict):
                nrc = r['nrc']
                if skip_errors:
                    # write `this_len` bytes of 0xFF to preserve offsets
                    f.write(b'\xFF' * this_len)
                    gap_count += this_len
                else:
                    print(f"\n[stop] 0x{addr:08X} NRC 0x{nrc:02X}")
                    break
            elif r is None:
                if skip_errors:
                    f.write(b'\xFF' * this_len)
                    gap_count += this_len
                else:
                    print(f"\n[stop] 0x{addr:08X} no response")
                    break
            else:
                f.write(r[:this_len])
                # pad if short
                if len(r) < this_len:
                    f.write(b'\xFF' * (this_len - len(r)))
            addr += this_len
            written += this_len
            # progress
            if written % (chunk * 32) == 0:
                elapsed = time.time() - t0
                rate = written / elapsed if elapsed > 0 else 0
                eta  = (length - written) / rate if rate > 0 else 0
                print(f"\r  0x{addr:08X}  {written}/{length} B  {rate:6.0f} B/s  ETA {eta/60:.1f}m  gaps={gap_count}",
                      end="", flush=True)
    print(f"\ndone — {written} bytes, {gap_count} bytes of gap/error padding")
    return written


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dll", default=r"C:\Program Files\TOPDON\J2534\FORD\RLink-FDRS.dll",
                    help="path to J2534 DLL")
    ap.add_argument("--ecu-req",  default="0x730", help="UDS request CAN ID (default 0x730)")
    ap.add_argument("--ecu-resp", default="0x738", help="UDS response CAN ID (default 0x738)")
    ap.add_argument("--baud", type=int, default=500000)
    ap.add_argument("--start",  required=True, help="start address (hex ok, e.g. 0x101D0000)")
    ap.add_argument("--length", required=True, help="length in bytes (hex ok)")
    ap.add_argument("--chunk",  type=int, default=64, help="bytes per ReadMemoryByAddress request (default 64)")
    ap.add_argument("--output", required=True, help="output .bin path")
    ap.add_argument("--no-skip", action="store_true", help="stop on first error (default: pad with 0xFF and continue)")
    args = ap.parse_args()

    start  = int(args.start, 0)
    length = int(args.length, 0)
    req_id = int(args.ecu_req, 0)
    resp_id = int(args.ecu_resp, 0)

    c = PSCMClient(args.dll, ecu_req=req_id, ecu_resp=resp_id, baud=args.baud)
    c.open()
    c.connect()
    print("[uds] extended session...")
    r = c.session(0x03)
    print(f"      -> {r.hex() if r else 'no response'}")
    print("[uds] tester present...")
    c.tester_present()
    print("[uds] strategy PN (F188):")
    print(f"      {(c.read_did(0xF188) or b'').decode('latin-1', errors='replace')!r}")
    print("[uds] cal PN (F10A):")
    print(f"      {(c.read_did(0xF10A) or b'').decode('latin-1', errors='replace')!r}")
    print(f"\n[dump] 0x{start:08X} .. 0x{start+length:08X}  ({length} bytes, {args.chunk} B/req)")
    dump_range(c, start, length, args.chunk, args.output, skip_errors=not args.no_skip)
    c.close()


if __name__ == "__main__":
    main()
