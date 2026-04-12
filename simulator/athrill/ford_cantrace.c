/*
 * Ford PSCM CAN injection + cal trace for Athrill2.
 *
 * Injects APA (0x3A8) and LKA (0x3CA) CAN messages into the RS-CAN
 * controller mailboxes, then runs AUTOSAR task entries and logs
 * every calibration read.
 */

#include "bus.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

uint32 cal_current_pc = 0;

/* Ford PSCM constants */
#define FORD_CAL_BASE      0x00FD0000u
#define FORD_STRATEGY_BASE 0x01000000u
#define FORD_EP_BASE       0x40010100u
#define FORD_SP_INIT       0x4001FF00u
#define FORD_CTBP          0x0100220Cu

#define REG_SP  3
#define REG_GP  4
#define REG_EP  30
#define REG_LP  31
#define SYSREG_CTBP  20

/* RS-CAN controller base */
#define CAN_BASE    0xFFD00000u

/* Read BE uint32 from bus */
static uint32 ford_read_be32(uint32 addr) {
    uint8 b[4];
    bus_get_data8(0, addr+0, &b[0]); bus_get_data8(0, addr+1, &b[1]);
    bus_get_data8(0, addr+2, &b[2]); bus_get_data8(0, addr+3, &b[3]);
    return ((uint32)b[0]<<24)|((uint32)b[1]<<16)|((uint32)b[2]<<8)|b[3];
}

/* Init table */
#define INIT_MARKER 0x001000EFu
static void ford_apply_init_table(void) {
    uint32 offset = FORD_STRATEGY_BASE + 0x9230;
    int count = 0;
    while (count < 100) {
        uint32 marker = ford_read_be32(offset);
        if (marker != INIT_MARKER) break;
        uint32 ram_end = ford_read_be32(offset+4);
        uint32 ram_start = ford_read_be32(offset+8);
        uint32 ctrl = ford_read_be32(offset+12);
        if (ram_end < ram_start) { offset += 16; count++; continue; }
        uint32 size = ram_end - ram_start + 1;
        uint8 op = (ctrl >> 24) & 0xFF;
        if ((op & 0xF0) == 0xA0) {
            uint32 a; for (a = ram_start; a <= ram_end; a++) bus_put_data8(0, a, 0);
        } else if (op == 0x01) {
            uint32 rom_src = ctrl & 0x00FFFFFF;
            if (rom_src < 0x01000000) rom_src += FORD_STRATEGY_BASE;
            uint32 j; for (j = 0; j < size; j++) {
                uint8 b; bus_get_data8(0, rom_src+j, &b); bus_put_data8(0, ram_start+j, b);
            }
        }
        offset += 16; count++;
    }
    printf("  Init table: %d entries\n", count);
}

/*
 * Inject CAN messages into RS-CAN controller mailboxes.
 * RH850 RS-CAN mailbox layout (simplified):
 *   Base + 0x0000: Global config
 *   Base + 0x0100: Mailbox 0 (16 bytes each)
 *     +0x00: ID register (bits 28:18 = standard ID)
 *     +0x04: DLC + flags
 *     +0x08: Data bytes 0-3
 *     +0x0C: Data bytes 4-7
 *
 * We write APA (0x3A8) into MB17 and LKA (0x3CA) into MB16.
 */
static void ford_inject_can(void) {
    /* Write CAN messages directly into RAM signal buffers.
     * The AUTOSAR COM stack copies CAN data from mailboxes into RAM buffers
     * during RX indication. Since we can't trigger the full CanIf/COM path,
     * we write directly to the RAM area where signals land.
     *
     * The ROM->RAM copy (init table entry 12) populates 0x40014490-0x4001CECF
     * with initial signal buffer data. The COM stack then updates these
     * during runtime. Let's also write vehicle speed into the CAN controller
     * mailboxes AND into likely RAM buffer locations.
     */

    /* CAN controller mailboxes (for code that polls hardware directly) */
    int mb;
    struct { uint32 id; uint32 d0; uint32 d1; } msgs[] = {
        /* BrakeSysFeatures 0x415: Veh_V_ActlBrk at bit7, 16bit BE, scale 0.01 */
        /* 2 kph = 200 in raw (200 * 0.01 = 2.0 kph) */
        {0x415, 0x00C80000, 0x00000000},  /* Veh_V_ActlBrk=200 (2.0 kph) */
        /* ParkAid_Data 0x3A8: APA handshake */
        {0x3A8, 0x46000000, 0x00000000},  /* SAPPStatusCoding=70 */
        /* Lane_Assist_Data1 0x3CA: LKA active */
        {0x3CA, 0x20000000, 0x00000000},  /* direction=2 */
        /* DesiredTorqBrk 0x213: vehicle stopped = 0 */
        {0x213, 0x00000000, 0x00000000},
        /* Yaw 0x091: yaw=0 */
        {0x091, 0x00000000, 0x00000000},
    };
    int num_msgs = sizeof(msgs)/sizeof(msgs[0]);

    for (mb = 0; mb < num_msgs; mb++) {
        uint32 mbox = CAN_BASE + 0x0100 + mb * 0x10;
        bus_put_data32(0, mbox + 0x00, msgs[mb].id << 18);
        bus_put_data32(0, mbox + 0x04, 0x00080001);
        bus_put_data32(0, mbox + 0x08, msgs[mb].d0);
        bus_put_data32(0, mbox + 0x0C, msgs[mb].d1);
    }

    /* Set all mailboxes as having new data */
    bus_put_data32(0, CAN_BASE + 0x0040, 0xFFFFFFFF);
    bus_put_data32(0, CAN_BASE + 0x0048, 0xFFFFFFFF);

    /* Also write vehicle speed into RAM areas that the COM stack would populate.
     * We don't know exactly where, but let's write the speed value (2.0 kph as
     * BE float = 0x40000000) into several likely RAM locations in the signal
     * buffer area. */
    uint32 speed_float_be = 0x40000000;  /* 2.0 as BE float */
    /* Write into the ROM->RAM data area at various offsets */
    /* These are guesses based on the init table destination range */
    uint32 sig_base = 0x40014490;
    uint32 sig_offsets[] = {0x100, 0x200, 0x400, 0x800, 0x1000, 0x2000};
    int si;
    for (si = 0; si < 6; si++) {
        bus_put_data32(0, sig_base + sig_offsets[si], speed_float_be);
    }
}

/* Strategy entry points — MainFunctions first, then tasks, then all entries */
static const uint32 entries[] = {
    /* Possible MainFunction dispatch entries (near CAN handler) */
    0x010872A6, 0x010872A8, 0x010872AA, 0x010872AC, 0x010872AE, 0x010872B0, 0x010872B2,
    /* CAN handler */
    0x01080000,
    /* BSW-area functions */
    0x01071626, 0x01075E68, 0x01076B94, 0x010772DC, 0x01077FB8,
    0x0107B6AA, 0x0107BE56, 0x0107D404, 0x0107FFC6,
    0x01085EAA, 0x010860D0, 0x010860D6, 0x010866CC,
    0x01087436, 0x0108824C, 0x010882E4, 0x01088454,
    0x01088738, 0x010892DA, 0x01089396, 0x0108AA2C,
    0x0108AD42, 0x0108B4BE, 0x0108BBEE, 0x0108EDAE,
    /* All other code entry points */
    0x01065BE6, 0x01068B32, 0x0106EF92, 0x0106F1C6,
    0x01071626, 0x01075E68, 0x01076B94, 0x010772DC,
    0x01077FB8, 0x0107B6AA, 0x0107BE56, 0x0107D404,
    0x0107FFC6, 0x01085EAA, 0x010860D0, 0x010860D6,
    0x010866CC, 0x010872A6, 0x010872A8, 0x010872AA,
    0x010872AC, 0x010872AE, 0x010872B0, 0x010872B2,
    0x01087436, 0x0108824C, 0x010882E4, 0x01088454,
    0x01088738, 0x010892DA, 0x01089396, 0x0108AA2C,
    0x0108AD42, 0x0108B4BE, 0x0108BBEE, 0x0108EDAE,
    0x01091558, 0x01091564, 0x0109168C, 0x01091CBC,
    0x01091CE0, 0x01091E92, 0x01092616, 0x0109271A,
    0x01092734, 0x01092766, 0x01092798, 0x010927B0,
    0x01092A5C, 0x01092A6A, 0x01092A8C, 0x01092A9A,
    0x010975DE, 0x0109763A, 0x0109790A, 0x01098590,
    0x01098C8E, 0x01099EBC, 0x0109C608, 0x0109EE30,
    0x010A048A, 0x010A1F4C, 0x010A1FA8, 0x010A1FFA,
    0x010A39AC, 0x010A4206, 0x010A462C, 0x010A5E70,
    0x010A7D80, 0x010A7E20, 0x010A7EEA, 0x010A8074,
    0x010A846C, 0x010AA01E, 0x010B0BB0, 0x010B0BDA,
    0x010B39DE, 0x010B45B8, 0x010B84AC, 0x010BA2F0,
    0x010BCE02, 0x010BFCC2, 0x010C13EA, 0x010C215A,
    0x010C3EBA, 0x010C41F2, 0x010C4230, 0x010C42C6,
    0x010C4444, 0x010C5C4C, 0x010C5CB0, 0x010C5E54,
    0x010C5FDA, 0x010C6160, 0x010C62E6, 0x010C646C,
    0x010C6784, 0x010C6F84, 0x010C737E, 0x010C7394,
    0x010C7A7A, 0x010C7A94, 0x010C7B1A, 0x010C7BDE,
    0x010C7DD4, 0x010C8384, 0x010CF970, 0x010D2220,
    0x010D2CDE, 0x010D45FC, 0x010D9146, 0x010DF4EC,
    0x010EA54C, 0x010FB27C,
    /* AUTOSAR tasks */
    0x010BA50C, 0x010BC360, 0x010DA378, 0x010CD53C,
};
#define NUM_ENTRIES (sizeof(entries)/sizeof(entries[0]))

/* Cal access log (from bus.h) */
extern uint32 cal_log_pc[];
extern uint32 cal_log_addr[];
extern uint32 cal_log_count;
extern int cal_log_enabled;

static void ford_setup_cpu(void) {
    extern CpuType virtual_cpu;
    TargetCoreType *core = &virtual_cpu.cores[0].core;

    printf("\n=== Ford PSCM CAN Trace ===\n");

    /* ROM stubs */
    uint32 s;
    for (s = 0xFFF20000; s < 0xFFF20200; s += 2) {
        bus_put_data8(0, s, 0x6D); bus_put_data8(0, s+1, 0x00);
    }

    /* Fill erased flash */
    {
        uint8 *rom_ptr = NULL;
        extern Std_ReturnType mpu_get_pointer(CoreIdType core_id, uint32 addr, uint8 **data);
        if (mpu_get_pointer(0, 0x00000800, &rom_ptr) == 0 && rom_ptr != NULL)
            memset(rom_ptr, 0xFF, 0x10000 - 0x800);
    }

    /* Apply init table */
    ford_apply_init_table();

    /* Apply RAM init table (zero-fill BSS + ROM→RAM copy) */
    ford_apply_init_table();

    /* Set AUTOSAR BSW init states (from autoas source + EP access analysis) */
    bus_put_data32(0, 0x40010100, 0x00030003);
    bus_put_data16(0, 0x40010102, 0x0003);
    bus_put_data32(0, 0x40010104, 0x00010001);
    bus_put_data16(0, 0x40010106, 0x0002);
    bus_put_data32(0, 0x40010108, 0x00020001);
    bus_put_data8(0, 0x4001010C, 0x01);
    bus_put_data8(0, 0x4001010E, 0x03);
    bus_put_data8(0, 0x40010110, 0x01);
    bus_put_data8(0, 0x40010112, 0x02);
    bus_put_data16(0, 0x40010118, 0x0003);
    bus_put_data8(0, 0x4001011E, 0x01);
    bus_put_data8(0, 0x40010120, 0x01);
    bus_put_data8(0, 0x4001012A, 0xFF);
    bus_put_data8(0, 0x4001012E, 0x01);
    bus_put_data16(0, 0x40010138, 0x0001);
    bus_put_data8(0, 0x40010140, 0x02);
    bus_put_data8(0, 0x40010142, 0x01);
    bus_put_data8(0, 0x40010145, 0x03);
    bus_put_data8(0, 0x40010146, 0x01);
    bus_put_data8(0, 0x40010150, 0xFF);
    bus_put_data8(0, 0x4001015E, 0x01);
    bus_put_data8(0, 0x40010160, 0x02);
    bus_put_data8(0, 0x40010161, 0x01);
    bus_put_data8(0, 0x40010165, 0x04);
    bus_put_data8(0, 0x40010168, 0x01);
    bus_put_data8(0, 0x4001016E, 0x01);
    bus_put_data8(0, 0x40010170, 0x03);
    bus_put_data8(0, 0x40010174, 0x01);
    bus_put_data8(0, 0x40010178, 0x01);
    bus_put_data8(0, 0x4001017E, 0x01);
    bus_put_data32(0, 0x40010180, 0x00030002);
    bus_put_data16(0, 0x40010182, 0x0003);
    bus_put_data16(0, 0x40010184, 0x0001);
    bus_put_data16(0, 0x400101A0, 0x0001);
    bus_put_data16(0, 0x400101C4, 0x0003);
    /* Fill remaining EP gaps with 0x01 */
    {
        uint32 a; uint8 v;
        for (a = 0x40010100; a < 0x40010500; a++) {
            bus_get_data8(0, a, &v);
            if (v == 0) bus_put_data8(0, a, 0x01);
        }
    }
    printf("  BSW state: AUTOSAR-correct init values set\n");

    /* Patch cal 0xFF areas with non-FF data to pass feature validation.
     * The firmware checks if feature cal data exists (reads and finds 0xFF = skip).
     * Write 0x00 to the checked offsets to trigger the feature code path.
     * Key offsets found by cal logging: 0x37C2, 0x6B74, 0x697C, 0x4501 */
    {
        uint8 *cal_ptr = NULL;
        extern Std_ReturnType mpu_get_pointer(CoreIdType core_id, uint32 addr, uint8 **data);
        if (mpu_get_pointer(0, FORD_CAL_BASE, &cal_ptr) == 0 && cal_ptr != NULL) {
            /* Fill all 0xFF areas in cal with 0x00 */
            uint32 i;
            for (i = 0; i < 0x10000; i++) {
                if (cal_ptr[i] == 0xFF) cal_ptr[i] = 0x00;
            }
            printf("  Cal: replaced all 0xFF with 0x00\n");
        }
    }

    /* Enable cal logging */
    cal_log_count = 0;
    cal_log_enabled = 1;

    /* Simulate AUTOSAR scheduler: run MainFunctions then Tasks in cycles */
    uint32 total_cal_reads = 0;
    uint32 ei;
    int cycle;

    /* Run 10 scheduler cycles */
    for (cycle = 0; cycle < 10; cycle++) {
    for (ei = 0; ei < NUM_ENTRIES; ei++) {
        uint32 entry = entries[ei];
        uint32 before = cal_log_count;

        /* Reset CPU */
        memset(core->reg.r, 0, sizeof(core->reg.r));
        core->reg.r[REG_SP] = FORD_SP_INIT;
        core->reg.r[REG_GP] = FORD_CAL_BASE;
        core->reg.r[REG_EP] = FORD_EP_BASE;
        core->reg.sys.grp[0][0].r[SYSREG_CTBP] = FORD_CTBP;
        core->reg.sys.grp[0][0].r[5] = 0x20;
        core->reg.pc = entry;
        core->is_halt = FALSE;

        /* Only inject CAN — DON'T reset BSW state. Let side effects accumulate. */
        ford_inject_can();

        /* For CAN handler (0x01080000), try passing message index as argument.
         * V850 calling convention: r6=arg1, r7=arg2, r8=arg3, r9=arg4.
         * The handler table index for APA(0x3A8)=0x0119, LKA(0x3CA)=0x0117.
         * Try setting r6 to different indices to see which triggers cal reads. */
        if (entry == 0x01080000) {
            /* Try APA index */
            core->reg.r[6] = 0x0119;  /* APA handler index */
            core->reg.r[7] = 0x03A8;  /* CAN ID */
            core->reg.r[8] = 8;       /* DLC */
        }

        /* Execute */
        int clocks;
        for (clocks = 0; clocks < 100000; clocks++) {
            if (core->is_halt) break;
            uint32 pc = core->reg.pc;
            if (pc < 0x01060000 || pc > 0x010FFFFF) {
                if (pc < 0x20FF0000 || pc > 0x21050000) break;
            }
            core->reg.r[0] = 0;
            extern Std_ReturnType cpu_supply_clock(CoreIdType core_id);
            if (cpu_supply_clock(0) != 0) core->reg.pc += 2;
        }

        uint32 new_reads = cal_log_count - before;
        if (new_reads > 0 || clocks > 100) {
            printf("  [%2u] 0x%08X: %u cal reads, %d clocks, end_pc=0x%08X\n",
                   ei, entry, new_reads, clocks, core->reg.pc);
        }
        total_cal_reads += new_reads;
    }
    if (total_cal_reads > 0) break; /* Stop if we found cal reads */
    } /* end cycle loop */

    /* Print cal access summary */
    printf("\n=== Cal Access Summary: %u total reads ===\n", total_cal_reads);

    if (cal_log_count > 0) {
        /* Collect unique cal offsets */
        printf("Unique cal offsets accessed:\n");
        uint32 i;
        /* Simple: just print first 200 unique (addr, pc) pairs */
        uint32 last_addr = 0xFFFFFFFF;
        uint32 printed = 0;
        for (i = 0; i < cal_log_count && printed < 300; i++) {
            uint32 cal_off = cal_log_addr[i] - FORD_CAL_BASE;
            if (cal_log_addr[i] != last_addr) {
                printf("  PC=0x%08X cal+0x%04X\n", cal_log_pc[i], cal_off);
                last_addr = cal_log_addr[i];
                printed++;
            }
        }
    }

    /* Restore registers for interactive session after exploration */
    core->reg.r[REG_SP] = FORD_SP_INIT;
    core->reg.r[REG_GP] = FORD_CAL_BASE;
    core->reg.r[REG_EP] = FORD_EP_BASE;
    core->reg.r[REG_LP] = 0;
    core->reg.sys.grp[0][0].r[SYSREG_CTBP] = FORD_CTBP;
    core->reg.sys.grp[0][0].r[5] = 0x20;
    core->is_halt = FALSE;

    printf("  Registers restored: EP=0x%08X GP=0x%08X SP=0x%08X\n",
           FORD_EP_BASE, FORD_CAL_BASE, FORD_SP_INIT);
    printf("\n=== Done ===\n");
    core->reg.pc = 0x010BA50C;
}
