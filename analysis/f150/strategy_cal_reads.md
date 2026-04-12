# F-150 PSCM Cal Reads Table

## Cal Base Address: 0x101D0000

Source file: cal_bdl_raw.bin (195,584 bytes = 0x2FC00 at base 0x101D0000)

## Note on Code Address Tracing

The strategy binary (ML3V-14D003-BD.VBF, loads at 0x10040000) does NOT contain  
direct MOVHI 0x101D instructions or embedded cal addresses. Cal access is done  
via runtime pointer indirection (AUTOSAR Rte_Prm pattern) initialized by the SBL.  
Code addresses for each cal read CANNOT be determined from static binary analysis.

## Confirmed Cal Offsets

| Cal Offset | Abs Address | Type | Current Value | Notes |
|---|---|---|---|---|
| +0x000C4 | 0x101D00C4 | float32 LE | 10.0 | LDW/LKA gate speed |
| +0x00114 | 0x101D0114 | float32 LE | 10.0 | LKA engage min speed (m/s) |
| +0x00120 | 0x101D0120 | float32 LE | 10.0 | LCA engage min speed (m/s) |
| +0x00140 | 0x101D0140 | float32 LE | 0.5  | APA engage min speed (kph) |
| +0x00144 | 0x101D0144 | float32 LE | 8.0  | APA engage max speed (kph) |
| +0x07ADC | 0x101D7ADC | u16 LE     | 10000 | LKA arm timer (10s @ 1ms tick) |
| +0x07ADE | 0x101D7ADE | u16 LE     | 10000 | LKA re-arm timer |
| +0x07E64 | 0x101D7E64 | u16 LE     | 10000 | ESA/TJA arm timer |

## Adjacent Timer Parameters

At cal+0x07AE0: u16=1500 (arm hysteresis?), u16=300 (related gate)  
At cal+0x07E66: u16=300, cal+0x07E68: u16=1500 (ESA related)
