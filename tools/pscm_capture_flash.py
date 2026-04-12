"""
Capture a live FORScan / FDRS flashing session and log every UDS frame to/from
the PSCM. The goal is to record seed/key exchanges (UDS service 0x27) so the
algorithm can be reversed from observed pairs.

Purely passive: this tool does not transmit anything. It listens on CAN and
records both directions of the PSCM UDS channel (default `0x730` / `0x738`).

Usage (32-bit Python + TOPDON RLink / Ford VCM-II):

    python tools/pscm_capture_flash.py \
        --dll "C:\\Program Files\\TOPDON\\J2534\\FORD\\RLink-FDRS.dll" \
        --output analysis/f150/flash_session.log

Then start FORScan and perform the flash sequence as normal. Every frame on
the UDS channel is recorded with a timestamp. The companion script
`pscm_seedkey_analyze.py` parses the log and extracts seed/key pairs.

The more (seed, key) pairs you collect, the easier the algorithm is to reverse.
Five pairs is usually enough. Try running `start`, `stop`, `start` on FORScan's
programming session a few times — each attempt generates a fresh seed.

This is legitimate observation of your own vehicle's bus traffic — analogous
to watching network packets on your own LAN. No reverse engineering of the
FORScan / FDRS binaries is performed.
"""
import argparse, ctypes, struct, time, sys


# J2534 protocol constants
CAN         = 5
PASS_FILTER = 1


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


def make_msg(proto, data):
    m = PASSTHRU_MSG()
    m.ProtocolID = proto
    m.DataSize = len(data)
    for i, b in enumerate(data):
        m.Data[i] = b
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dll", default=r"C:\Program Files\TOPDON\J2534\FORD\RLink-FDRS.dll",
                    help="J2534 DLL path")
    ap.add_argument("--baud", type=int, default=500000, help="CAN baud (default 500k)")
    ap.add_argument("--req",  default="0x730", help="UDS request CAN ID to capture (default 0x730)")
    ap.add_argument("--resp", default="0x738", help="UDS response CAN ID to capture (default 0x738)")
    ap.add_argument("--output", required=True, help="log file path")
    args = ap.parse_args()

    req  = int(args.req, 0)
    resp = int(args.resp, 0)
    dll = ctypes.WinDLL(args.dll)

    dev = ctypes.c_ulong(0)
    if dll.PassThruOpen(None, ctypes.byref(dev)) != 0:
        sys.exit("PassThruOpen failed")
    print(f"[j2534] device {dev.value}")

    ch = ctypes.c_ulong(0)
    if dll.PassThruConnect(dev, CAN, 0, args.baud, ctypes.byref(ch)) != 0:
        sys.exit("PassThruConnect failed")
    # pass-all filter so we see both directions
    mask    = make_msg(CAN, struct.pack('>I', 0))
    pattern = make_msg(CAN, struct.pack('>I', 0))
    filt = ctypes.c_ulong(0)
    if dll.PassThruStartMsgFilter(ch, PASS_FILTER,
                                  ctypes.byref(mask), ctypes.byref(pattern),
                                  None, ctypes.byref(filt)) != 0:
        sys.exit("PassThruStartMsgFilter failed")
    print(f"[j2534] channel {ch.value}, pass-all filter {filt.value}")

    print(f"[capture] writing to {args.output}")
    print(f"[capture] watching CAN IDs 0x{req:03X} and 0x{resp:03X}")
    print("[capture] Start your FORScan flash session now. Ctrl-C to stop.\n")

    t0 = time.time()
    written = 0
    try:
        with open(args.output, 'w') as f:
            f.write(f"# pscm flash session capture\n# req=0x{req:03X} resp=0x{resp:03X} baud={args.baud}\n")
            while True:
                msg = PASSTHRU_MSG()
                n = ctypes.c_ulong(1)
                if dll.PassThruReadMsgs(ch, ctypes.byref(msg), ctypes.byref(n), 1000) == 0 and n.value > 0:
                    if msg.DataSize < 4:
                        continue
                    cid = struct.unpack_from('>I', bytes(msg.Data[:4]))[0]
                    payload = bytes(msg.Data[4:msg.DataSize])
                    direction = None
                    if cid == req:  direction = 'TX'  # tester -> PSCM
                    elif cid == resp: direction = 'RX'  # PSCM -> tester
                    if direction is None:
                        continue
                    t = time.time() - t0
                    f.write(f"{t:10.4f}  {direction}  0x{cid:03X}  {payload.hex()}\n")
                    f.flush()
                    written += 1
                    # live tap: flag 0x27 seed/key exchanges
                    if len(payload) >= 2 and payload[0] == 0x27 or (len(payload) >= 3 and payload[0] == 0x67):
                        print(f"  [{t:6.2f}s] {direction} 0x{cid:03X} {payload.hex()}  <-- 0x27 SecurityAccess")
                    elif len(payload) >= 1 and payload[0] == 0x10:
                        print(f"  [{t:6.2f}s] {direction} 0x{cid:03X} {payload.hex()}  (session control)")
                    elif len(payload) >= 2 and payload[0] == 0x50:
                        print(f"  [{t:6.2f}s] {direction} 0x{cid:03X} {payload.hex()}  (session control resp)")
    except KeyboardInterrupt:
        print(f"\n[capture] done, {written} frames written to {args.output}")
    finally:
        try: dll.PassThruDisconnect(ch)
        except Exception: pass
        try: dll.PassThruClose(dev)
        except Exception: pass


if __name__ == "__main__":
    main()
