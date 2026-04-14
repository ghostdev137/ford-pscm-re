# Agent brief — extract Ford SA level 0x01 algorithm for Transit PSCM

**Where you are:** Windows PC with both **ForScan** and **FDRS** installed. Both can flash a 2025 Ford Transit PSCM (module SW `KK21-14D003-AM`). That means both binaries contain the SecurityAccess level 0x01 seed→key algorithm for the KK21 module family — that's what we need to extract.

**Why:** On a live Transit PSCM we captured the UDS `0x27 0x01` seed (`38be1b5fcbfef6d8a6162b2931592d26`, 16 bytes) but panda dropped the `0x27 0x02 <key>` reply during the busy flash-entry window, so we can't recover the key from the bus alone. Unlocking SA level 0x01 lets us push a custom SBL over `0x34/0x36/0x37` and dump the mask-ROM PBL that isn't in any VBF — which unblocks our RH850 G3KH Ghidra analysis.

The seed is 16 bytes, key is 16 bytes → almost certainly **AES-128** (or an AES-derived construct like CMAC). The algorithm is usually:
```
key = AES128_Encrypt(seed, K) ^ C     (or some variant)
```
where `K` is a fixed per-module-family constant ("SecurityAccess key") and `C` is optionally a constant mask.

## What to deliver

1. The **raw SA algorithm bytes** for the Ford KK21 / Transit PSCM family: the 128-bit key `K`, any constant mask, and the exact operation order.
2. A **standalone Python script** `sa_kk21.py` that takes a 16-byte seed hex string and prints the 16-byte key. Verify it against the known pair:
   - Seed `a7c78c5410e42e2b9b9d1f3423d57b88` → Key `276975aa993e61388df73ff337a6fbd0` (level 0x03, already captured)
3. A short writeup: which binary the algo lives in, offset, function-identifying characteristics.

## Where to look

### FDRS (preferred — Ford's official dealer tool)
- Typical install: `C:\Program Files\Ford Motor Company\FDRS\` or similar.
- Core executables/DLLs that handle module reflash. Look for names containing `PSCM`, `KK21`, `flash`, `reprogram`, `uds`, `security`.
- FDRS may ship a **per-module "Strategy File" or XML manifest** that references the algo DLL.
- FDRS ships with a large **module database** — search it for `KK21` / `14D003` / the PSCM AS-BUILT file name. The matching DLL likely contains the algo.

### ForScan
- Typical install: `C:\Program Files (x86)\ForScan\`.
- Flash logic usually in main exe or a plugin DLL in the install dir.
- ForScan is smaller than FDRS — easier to reverse, but some modern SA algos are only in FDRS.

## How to find the algorithm

1. **Strings search** each binary for: `aesenc`, `AES_`, `sbox`, `Rijndael`, `SecurityAccess`, `0x27`, `seed`, `key`. Short matches alone don't prove anything but they map out candidate DLLs.
2. **AES S-box fingerprint** — every AES impl contains the forward S-box starting `63 7C 77 7B F2 6B 6F C5 30 01 67 2B FE D7 AB 76`. Grep each DLL's `.rdata` for that byte sequence. Whichever DLL contains the S-box is where the AES lives.
3. Once you find the AES S-box, look **near it in the same section** for a **16-byte constant** that's the module key `K`. Ford typically stores it plainly in `.rdata` right next to the AES tables.
4. Disassemble functions that reference both the S-box and the key constant. One of them will be the seed→key transform. Read its structure.
5. If `K` is obfuscated/derived at runtime (Ford sometimes XORs it with a per-module string), dump the relevant strings too — the module SW number `KK21-14D003-AM` is a likely salt ingredient.

## Tools available on the PC
- **IDA / Ghidra** for static RE — pick whichever is installed. Ghidra is free.
- **Windbg / x64dbg** if you need dynamic (attach to ForScan during a mock flash, set bp on AES function, dump K from registers). This works but is slower.
- **PE-bear / CFF Explorer** for section layout.
- **strings.exe** (Sysinternals) for quick string dumps.

## Validation

Once you think you have the algo, verify BEFORE reporting success:

```
seed: a7c78c5410e42e2b9b9d1f3423d57b88
key:  276975aa993e61388df73ff337a6fbd0    (SA level 0x03 sub=0x04)
```

If your implementation produces the key from the seed, you've got it. **Level 0x03 (extended) and level 0x01 (programming) may use different keys or different algo variants** — confirm for 0x01 separately. If only 0x03 reproduces, you still need to find the 0x01 variant. Search for two similar-looking functions or a single function with a level/sub-function switch.

## Other known pairs (may help cross-check)

- SA 0x03: seed `a7c78c5410e42e2b9b9d1f3423d57b88` key `276975aa993e61388df73ff337a6fbd0` ✅ verified full pair
- SA 0x03: key `8579344f2d8197a62b25ffbb73ab1e4f` (seed not captured)
- SA 0x01: seed `38be1b5fcbfef6d8a6162b2931592d26` (key not captured — is what we want to derive)

All from Transit VIN `1FTBFB8XG0SKA969007`, PSCM `KK21-14D003-AM`.

## Out of scope

- Don't touch the vehicle. This is static RE only.
- Don't publish the extracted key. Dealer-tool algorithms are legally gray; keep findings local.
- Don't modify the Windows install — work from copies only.

## Reporting back

Commit findings to this repo in `~/ford-pscm-re/analysis/sa_kk21/`:
- `sa_kk21.py` — the reimplementation
- `notes.md` — which binary, offset, function addr, how you found it, any Ford-specific quirks
- `test_vectors.txt` — the seed/key pairs above plus any you generate

Return path: push to whichever branch the repo is on.
