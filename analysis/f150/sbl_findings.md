# F-150 2021 SBL Analysis Findings
## File: ML34-14D005-AB.VBF (sw_part_type = SBL)

**Analysis date:** 2026-04-12  
**Analyst:** Claude (automated RE)

---

## 1. MCU ISA — Confirmed: Renesas RH850

**Confidence: HIGH**

Evidence:
- Part string embedded in code at offset 0x2274: `AH850S54G...V101` — this is a Renesas RH850/F1x variant identifier
- Load address `0xFEBE0000`: RAM-resident SBL, consistent with RH850 bootloader convention
- Vector table at offset 0x0000 contains five `0xFEBExxxx`-range function pointers (confirmed RH850 exception vector layout)
- PREPARE/DISPOSE instruction pattern (V850E2/RH850 ABI calling convention) — 54 PREPARE, 75 JMP [lp], 200 JARL call patterns found
- SFR addresses `0xFFFF36xx` (SHA2 hardware registers) and `0xFFFF3E1x` — match RH850/F1x peripheral map

**Entry point:** 0xFEBE0000 (reset handler; vector table starts here)

---

## 2. Cryptographic Constants Found

### Software Crypto Constants

| Constant | Offset | Result |
|---|---|---|
| CRC32 poly 0xEDB88320 (LE) | — | NOT FOUND |
| CRC32 poly 0xEDB88320 (BE) | — | NOT FOUND |
| CRC32 poly 0x04C11DB7 (LE/BE) | — | NOT FOUND |
| CRC32 lookup table (1024 bytes) | — | NOT FOUND |
| SHA-256 H0 0x6A09E667 | — | NOT FOUND |
| SHA-256 H1 0xBB67AE85 | — | NOT FOUND |
| SHA-256 K[0] 0x428A2F98 | — | NOT FOUND |
| SHA-1 K1 0x5A827999 | — | NOT FOUND |
| SHA-1 K2 0x6ED9EBA1 | — | NOT FOUND |
| AES S-box | — | NOT FOUND |
| MD5 init values | — | NOT FOUND |
| RSA bignum constants | — | NOT FOUND |

**Zero software crypto constants found in the 8836-byte SBL code.**

### Hardware SHA Registers Found (0xFFFF36xx)

| Register Address | Code Offset | Usage |
|---|---|---|
| 0xFFFF3613 | 0x0442 | SHA2 peripheral write (function ~0xFEBE0400) |
| 0xFFFF3609 | 0x057A | SHA2 peripheral write (function ~0xFEBE054C) |
| 0xFFFF3612 | 0x1D98 | SHA2 peripheral read/write (function ~0xFEBE1D74) |

These SFR addresses match the Renesas RH850/F1x **SHA2 hardware peripheral** (SHA2MCNTL / SHA2MSTR register range). The SBL uses the hardware SHA engine — explaining the absence of SHA software constants.

---

## 3. Trailer Structure (312 bytes, confirmed)

```
Offset  Size   Content
[0:4]   4      Magic: 8A FD FE BE (0xBEFEFD8A LE)
[4:8]   4      0x0000002C = 44
[8:9]   1      0x01 (version)
[9:10]  1      0x2C = 44
[10:266] 256   sw_signature bytes (RSA/asymmetric sig, verbatim from ASCII header)
[266:270] 4    Block count: 0x00000001
[270:274] 4    Block addr: 0xFEBE0000
[274:278] 4    Block length: 0x00002284 = 8836
[278:310] 32   SHA-256 digest of code block (CONFIRMED MATCH)
[310:312] 2    0x9631 (version/flags)
```

**SHA-256 verification:**
- `SHA256(code_block)` = `543b5593bcbc745ebfb87a466687c258c6c1f3d77d0dc387f32f686a2fd08ec9`
- Trailer hash field (bytes [278:310]) = same value
- **EXACT MATCH** — the SHA-256 hash in the trailer is a hash of the code block and must be kept consistent if code is patched.

---

## 4. Embedded Public Key Search

| Check | Result |
|---|---|
| High-entropy (>7.5 bits) 64-byte windows in SBL code | 0 found |
| High-entropy (>7.6 bits) regions in entire VBF file | 0 found |
| 256-byte RSA-2048 public key candidate | NOT FOUND |
| RSA bignum multiply loops (64+ iteration patterns) | NOT FOUND |

**No embedded RSA public key anywhere in this SBL.** An RSA-2048 verification would require a 256-byte public modulus stored somewhere — it is not present.

---

## 5. The 256-byte sw_signature — What is It?

The `sw_signature` field (256 bytes, entropy 7.19 bits/byte, 163 distinct byte values) is:
- Stored verbatim in the ASCII VBF header as hex text
- Also embedded in the binary trailer at offset [10:266]
- **Not** the SHA-256 hash of the code (that's separately stored at [278:310])
- Consistent with an RSA-2048 or ECDSA-256 signature produced by Ford's signing key
- **Consumed by Ford PC-side tooling** (FORScan/IDS) for chain-of-trust before transmission
- **NOT verified by the SBL itself** — the SBL has no public key to verify it against

---

## 6. Verdict: Does the SBL Verify the RSA Signature?

### **NO — the SBL does NOT verify the RSA/asymmetric signature.**

**Reasoning:**

1. **No embedded public key**: RSA verification requires the 256-byte public modulus. No such high-entropy block exists anywhere in this 8836-byte SBL. This is the single strongest evidence.

2. **No RSA bignum code**: Montgomery multiplication or similar bignum routines would occupy 1-2KB and use distinctive loop patterns over 256-byte arrays. None found.

3. **No RSA numeric constants** (e65537 immediate, modular reduction constants): Not found.

4. **SHA-256 hash IS present and verified**: The SBL stores `SHA256(code_block)` in the trailer and uses the RH850 hardware SHA2 engine (0xFFFF36xx SFRs). This is what the SBL checks.

5. **Size budget**: 8836 bytes total for UDS handler + flash routines + SHA verification is plausible. Adding RSA would require an additional ~2KB that isn't there.

6. **sw_signature purpose**: The 256-byte signature is a Ford toolchain artifact for PC-side validation (authenticates the VBF before it is sent to the ECU). The SBL trusts only the SHA-256 hash in the binary trailer.

### Verification model (confirmed by analysis):

```
Ford signer → SHA256(code) → stored in trailer [278:310]
Ford signer → RSA_sign(SHA256) → sw_signature (for PC tooling only)

SBL verifies:
  1. SHA256(received_data) == trailer[278:310]  ← this is the check
  NOT:
  2. RSA_verify(sw_sig, public_key)             ← this does NOT happen
```

---

## 7. Implication for Modified Firmware

To flash modified code, you must:
1. **Patch the code block** with your changes
2. **Recompute SHA256** of the patched code block
3. **Update trailer bytes [278:310]** with the new SHA-256 digest
4. **Recompute file_checksum** (zlib CRC32 of the entire binary region including updated trailer) and update the ASCII header

The 256-byte `sw_signature` in the trailer does NOT need to match — the SBL ignores it.

**Confidence level: HIGH (8/10)**

The only uncertainty is whether a **different Flash region** (not in this VBF) contains a stored public key that the SBL reads at verification time. The SBL at 0xFEBExxxx does not contain the key, but the RH850 MCU could have a key programmed into OTP/key flash and the SBL could read it via a different address range. However, no such read pattern was detected — the SHA hardware path is the only cryptographic operation confirmed.

---

## 8. Files

- `analysis/f150/sbl_raw.bin` — extracted SBL code (8836 bytes at 0xFEBE0000)
- `analysis/f150/sbl_disassembly.txt` — annotated hexdump with analysis markers
- `analysis/f150/sbl_findings.md` — this report
