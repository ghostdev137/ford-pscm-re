# Transit PSCM LCA Hunt — 0x3CC TX / 0x3D6 RX Gate

**Binary:** `transit_AM_blk0_0x01000000.bin.bndb`
**Segment:** 0x1000000–0x10FFFF0 (1 MB, single executable block)
**Architecture:** V850E3 / RH850 (little-endian RISC, 2- and 4-byte instructions)
**Date:** 2026-04-14

---

## 1. 0x3CC TX Function — Lane_Assist_Data3_FD1

### PDU Registration

| Address     | Raw bytes            | Interpretation |
|-------------|----------------------|----------------|
| `0x1002b78` | `03 CC 01 27 03 08 00 00` | CAN ID 0x3CC (BE), network=0x01, PDU_idx=0x27, type=TX(0x03), DLC=8 |

The table at **`0x1002b50`** (renamed `CAN_PDU_DescriptorTable`, called from `CAN_Stack_Init` @ `0x1002ad8`) is the AUTOSAR ComStack PDU descriptor table. Entry format (8 bytes):

```
{ canId_BE:16, network:8, pduIdx:8, type:8 [TX=0x03 / RX=0x01], dlc:8, pad:16 }
```

0x3CC is registered at `0x1002b78` with **handle 0x0127** (PDU index 0x27).

### TX Task Call Chain

| Address      | Renamed Symbol         | Role |
|--------------|------------------------|------|
| `0x1090a78`  | `CAN_TX_Task_20ms`     | RTOS task entry — no listed callers, calls CAN_TX_Dispatch_A + sub_1090b70. Contains writes `*(arg+0x400)` and `*(arg+0x800)` (candidate RSCANFD channel regs). |
| `0x1090c60`  | `CAN_TX_Dispatch_A`    | Called by CAN_TX_Task_20ms, tailcalls CAN_TX_Dispatch_B. |
| `0x1090ce4`  | `CAN_TX_Dispatch_B`    | Large dispatch (~54 KB disasm). Uses `callt` for indirect AUTOSAR ComStack calls via CTB vector table at 0xFFF00050. Calls sub_1081dca, sub_108bdac, sub_10912ac, sub_1082dd6, sub_10aed5a. **Candidate PDU assembly dispatcher for 0x3CC group.** |

### Hardware Write Layer

| Address      | Renamed Symbol               | Role |
|--------------|------------------------------|------|
| `0x10977e8`  | `RSCANFD_ChannelDispatcher`  | 0x58+ switch cases, no listed callers (indirect via function pointer table at 0x100a268). case 2 → RSCANFD_WritePDU_candidate; case 5 → direct RSCANFD reg writes at offsets 0x7010/0x1452 from r29. |
| `0x1087850`  | `RSCANFD_WritePDU_candidate` | Contains `st.w r8, 0x7010[r29]` and `st.w r8, 0x1450[r29]` — RSCANFD message buffer register writes. Called from sub_1087744 and RSCANFD_ChannelDispatcher case 2. Function pointer table at 0x100a268 contains BE pointer `0x010878DA` into this function region. |

### Confidence Assessment

- **PDU registration:** HIGH. 0x3CC is definitively registered at 0x1002b78, handle 0x0127.
- **TX task entry:** MEDIUM-HIGH. CAN_TX_Task_20ms (0x1090a78) is the root CAN TX RTOS task based on call graph position and RSCANFD register write pattern.
- **Exact PDU assembly function:** MEDIUM. CAN_TX_Dispatch_B (0x1090ce4) is the best candidate for the PDU assembly/signal-packing dispatcher, but V850 disassembly is heavily garbled (SLEIGH decoder issues with interleaved code). The `callt` pattern confirms AUTOSAR ComStack indirect dispatch — the actual signal-packing stub is called via CTB vector, making it hard to isolate by static analysis alone.
- **Note on byte-pattern search:** Searching for LE bytes `CC 03` and `03 CC` in the code section yielded only false positives (embedded in V850 instruction encodings as displacements). The firmware accesses RSCANFD (base 0xFFD00000) via CALLT vector table — no standalone `0xFFD0` literals are emitted in the function bodies.

---

## 2. 0x3D6 RX Gate — LateralMotionControl2

### Definitive Finding: Not Registered

A full scan of the CAN PDU descriptor table (0x1002b50–0x1002D70, sentinel `0x47FF`) reveals:

| Offset      | CAN ID (BE) | Direction |
|-------------|-------------|-----------|
| `0x1002C88` | `03 CA` = 0x3CA | TX |
| `0x1002C90` | `03 B3` = 0x3B3 | TX |

**CAN ID 0x3D6 is absent.** The table skips from 0x3CA directly to 0x3B3 with no 0x3D6 entry. The gate is at the **CAN stack routing registration level** — the PDU for LateralMotionControl2 was never registered in the CAN driver init data.

### Byte Pattern Search Results (all false positives)

Searches for `d6 03` (LE) and `03 d6` (BE) in the text segment:

| Address     | Context | Verdict |
|-------------|---------|---------|
| `0x103d3e0` | In sub_103d36e: `sld.h 0xd6[ep], r16` at 0x103d373 | FALSE POSITIVE — 0xD6 is an EP-relative displacement |
| `0x1043c03` | `78 03 d6 27 51 4d` in sub_1043980 | FALSE POSITIVE — V850 instruction encoding |
| `0x1060d19` | `2e XX` repeating structured table pattern | FALSE POSITIVE — table data, `d6 03` is a table entry value |
| `0x1066320` | `2e XX` repeating pattern | FALSE POSITIVE — same structured table pattern |
| `0x10847d2` | `79 ff d6 03 7c 00 01 46` — likely `ld.bu 0xFFD6[r25]` | FALSE POSITIVE — 0xFFD6 = -42 signed displacement |

**No code-level RX handler for 0x3D6 was found.** There is no in-code `NvM`/calibration gate check to unlock — the message simply does not exist in the CAN routing layer.

### Gate Variable: Not Located

The absence from the PDU table is the complete gate. There is no additional application-layer guard variable identified. The `NVRAMManager/NvM_main.c` string at 0x1002a80 (immediately before the PDU table) is likely a debug source-path string embedded by the linker, not a functional gate.

---

## 3. Path to Enabling 0x3D6

To receive LateralMotionControl2 (0x3D6) in this firmware, a new PDU descriptor entry must be injected into the table at 0x1002b50. The entry to add:

```
03 D6 01 XX 01 08 00 00
```

Where `XX` = next available PDU index (inspect table to find highest existing RX index + 1). The RX handler code would also need to be implemented or pointed at an existing stub — no dormant handler was found.

---

## 4. Binary Ninja Annotations Applied

| Address     | Type    | Action |
|-------------|---------|--------|
| `0x1002b48` | Function | Renamed → `CAN_PDU_DescriptorTable` |
| `0x1002ad8` | Function | Renamed → `CAN_Stack_Init` |
| `0x1002b50` | Address comment | PDU table structure description + 0x3D6 absence note |
| `0x1002b78` | Address comment | 0x3CC entry annotation (handle, signals, cycle time) |
| `0x1090a78` | Function | Renamed → `CAN_TX_Task_20ms` + function comment |
| `0x1090c60` | Function | Renamed → `CAN_TX_Dispatch_A` |
| `0x1090ce4` | Function | Renamed → `CAN_TX_Dispatch_B` + function comment |
| `0x1087850` | Function | Renamed → `RSCANFD_WritePDU_candidate` + function comment |
| `0x10977e8` | Function | Renamed → `RSCANFD_ChannelDispatcher` + function comment |

---

## 5. Open Threads / Next Steps

1. **Confirm PDU assembly stub:** The `callt` dispatch within CAN_TX_Dispatch_B (0x1090ce4) calls through the CTB vector table at 0xFFF00050. Read the CTB vector table to map `callt 0`, `callt 0x1`, `callt 0x9`, `callt 0x21` to their handler addresses — one of these will be the 0x3CC signal-packing stub.

2. **Map RSCANFD function pointer table:** Table at 0x100a268 contains BE code pointers in the 0x010878xx range pointing into RSCANFD_WritePDU_candidate region. Decode all entries to map channel→handler for each CAN bus.

3. **Inject 0x3D6 entry:** If enabling LCA RX, add PDU entry at end of table (before 0x47FF sentinel at ~0x1002D70) and implement/redirect the RX callback.

4. **Verify sub_1084dfa cluster:** This function (no listed callers, calls 23 sub-functions including sub_1082dd6 which is also in CAN_TX_Dispatch_B's callee list) may be a parallel TX handler or CAN error manager. Worth tracing.
