#!/usr/bin/env python3
"""LZSS encoder — exact port of qvbf encoder from vbf_tool.js.

Params: EI=10, EJ=4, P=1, N=1024, F=17.
"""

EI, EJ, P = 10, 4, 1
N = 1 << EI          # 1024
F = (1 << EJ) + P    # 17


def lzss_encode(data: bytes) -> bytes:
    buffer = bytearray(N * 2)   # init to 0 per qvbf port
    bit_buffer = 0
    bit_mask = 128
    output = bytearray()

    def putbit1():
        nonlocal bit_buffer, bit_mask
        bit_buffer |= bit_mask
        bit_mask >>= 1
        if bit_mask == 0:
            output.append(bit_buffer & 0xff)
            bit_buffer = 0
            bit_mask = 128

    def putbit0():
        nonlocal bit_buffer, bit_mask
        bit_mask >>= 1
        if bit_mask == 0:
            output.append(bit_buffer & 0xff)
            bit_buffer = 0
            bit_mask = 128

    def output1(c):
        putbit1()
        mask = 256
        while True:
            mask >>= 1
            if mask == 0:
                break
            if c & mask:
                putbit1()
            else:
                putbit0()

    def output2(x, y):
        putbit0()
        mask = N
        while True:
            mask >>= 1
            if mask == 0:
                break
            if x & mask:
                putbit1()
            else:
                putbit0()
        mask = (1 << EJ)
        while True:
            mask >>= 1
            if mask == 0:
                break
            if y & mask:
                putbit1()
            else:
                putbit0()

    # Initial fill
    data_idx = 0
    bufferend = N - F
    for i in range(N - F, N * 2):
        if data_idx >= len(data):
            break
        buffer[i] = data[data_idx]
        data_idx += 1
        bufferend = i + 1

    r = N - F
    s = 0

    while r < bufferend:
        f1 = F if (F <= bufferend - r) else (bufferend - r)
        x = 0
        y = 1
        c = buffer[r]

        for i in range(r - 1, s, -1):
            if (s >= (r - i)) and buffer[i] == c:
                j = 1
                while j < f1:
                    if buffer[i + j] != buffer[r + j]:
                        break
                    j += 1
                if j > y:
                    x = i
                    y = j

        if x >= (N - F):
            x -= (N - F)
        x += 1

        if y <= P:
            output1(c)
        else:
            output2(x & (N - 1), y - 2)

        r += y
        s += y

        if r >= N * 2 - F:
            for i in range(N):
                buffer[i] = buffer[i + N]
            bufferend -= N
            r -= N
            s -= N
            while bufferend < N * 2:
                if data_idx >= len(data):
                    break
                buffer[bufferend] = data[data_idx]
                data_idx += 1
                bufferend += 1

    if bit_mask != 128:
        output.append(bit_buffer & 0xff)

    return bytes(output)


if __name__ == '__main__':
    import sys, os, time
    sys.path.insert(0, '/Users/rossfisher/ford-pscm-re/tools')
    from vbf_decompress import lzss_decode
    for f in ['/tmp/pscm/transit_AM_blk1_0x10000400.bin',
              '/tmp/pscm/transit_AM_blk2_0x20FF0000.bin',
              '/tmp/pscm/transit_AM_blk0_0x01000000.bin']:
        d = open(f, 'rb').read()
        t = time.time()
        enc = lzss_encode(d)
        elapsed = time.time() - t
        dec = lzss_decode(enc)
        ok = dec == d
        print(f'{os.path.basename(f)}: {len(d)}B -> {len(enc)}B ({elapsed:.1f}s) roundtrip={ok}')
        if not ok:
            for i in range(min(len(d), len(dec))):
                if d[i] != dec[i]:
                    print(f'  diff @{i}: orig={d[i]:02x} dec={dec[i]:02x}')
                    break
