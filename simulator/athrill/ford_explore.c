/*
 * Ford PSCM multi-entry exploration for Athrill2.
 *
 * Runs each strategy function entry point for N clocks,
 * tracks unique PCs visited, reports coverage.
 *
 * Replaces ford_setup_cpu() — #include this instead.
 */

#include "bus.h"
#include <string.h>
#include <stdio.h>

/* Ford PSCM constants */
#define FORD_CAL_BASE      0x00FD0000
#define FORD_STRATEGY_BASE 0x01000000
#define FORD_EP_BASE       0x40010100
#define FORD_SP_INIT       0x4001FF00
#define FORD_CTBP          0x0100220C

#define REG_SP  3
#define REG_GP  4
#define REG_EP  30
#define REG_LP  31
#define SYSREG_CTBP  20

/* Coverage tracking */
#define COVERAGE_HASH_SIZE  (1 << 18)  /* 256K entries */
static uint32 coverage_hash[COVERAGE_HASH_SIZE];
static uint32 coverage_count = 0;

static void coverage_reset(void) {
    memset(coverage_hash, 0, sizeof(coverage_hash));
    coverage_count = 0;
}

static int coverage_add(uint32 pc) {
    uint32 idx = (pc >> 1) & (COVERAGE_HASH_SIZE - 1);
    /* Linear probing */
    int i;
    for (i = 0; i < 16; i++) {
        uint32 slot = (idx + i) & (COVERAGE_HASH_SIZE - 1);
        if (coverage_hash[slot] == 0) {
            coverage_hash[slot] = pc;
            coverage_count++;
            return 1;  /* new */
        }
        if (coverage_hash[slot] == pc) {
            return 0;  /* already seen */
        }
    }
    return 0;
}

/* Strategy code entry points */
static const uint32 strategy_entries[] = {
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
    /* AUTOSAR task entries */
    0x010BA50C, 0x010BC360, 0x010DA378, 0x010CD53C,
};
#define NUM_ENTRIES (sizeof(strategy_entries)/sizeof(strategy_entries[0]))

static void ford_setup_cpu(void)
{
    extern CpuType virtual_cpu;
    TargetCoreType *core = &virtual_cpu.cores[0].core;

    printf("\n=== Ford PSCM V850E2M Exploration ===\n");

    /* ROM stubs */
    uint32 stub_addr;
    for (stub_addr = 0xFFF20000; stub_addr < 0xFFF20200; stub_addr += 2) {
        bus_put_data8(0, stub_addr, 0x6D);
        bus_put_data8(0, stub_addr + 1, 0x00);
    }

    /* Fill erased flash */
    {
        uint8 *rom_ptr = NULL;
        extern Std_ReturnType mpu_get_pointer(CoreIdType core_id, uint32 addr, uint8 **data);
        if (mpu_get_pointer(0, 0x00000800, &rom_ptr) == 0 && rom_ptr != NULL) {
            memset(rom_ptr, 0xFF, 0x10000 - 0x800);
        }
    }

    /* Run each entry */
    coverage_reset();
    uint32 total_new = 0;
    uint32 entry_idx;

    for (entry_idx = 0; entry_idx < NUM_ENTRIES; entry_idx++) {
        uint32 entry = strategy_entries[entry_idx];
        uint32 before = coverage_count;

        /* Reset CPU state */
        memset(core->reg.r, 0, sizeof(core->reg.r));
        core->reg.r[REG_SP] = FORD_SP_INIT;
        core->reg.r[REG_GP] = FORD_CAL_BASE;
        core->reg.r[REG_EP] = FORD_EP_BASE;
        core->reg.r[REG_LP] = 0;
        core->reg.sys.grp[0][0].r[SYSREG_CTBP] = FORD_CTBP;
        core->reg.sys.grp[0][0].r[5] = 0x20;  /* PSW */
        core->reg.pc = entry;
        core->is_halt = FALSE;

        /* Pre-fill EP area */
        uint32 addr;
        for (addr = FORD_EP_BASE; addr < FORD_EP_BASE + 0x200; addr++) {
            bus_put_data8(0, addr, 0x01);
        }

        /* Execute N clocks */
        int clocks;
        for (clocks = 0; clocks < 10000; clocks++) {
            if (core->is_halt) break;
            uint32 pc = core->reg.pc;
            /* Skip if PC in data area or unmapped */
            if (pc < 0x01060000 || pc > 0x010FFFFF) {
                if (pc < 0x20FF0000 || pc > 0x21050000) {
                    break;
                }
            }
            coverage_add(pc);
            core->reg.r[0] = 0;

            /* Step one instruction */
            extern Std_ReturnType cpu_supply_clock(CoreIdType core_id);
            Std_ReturnType err = cpu_supply_clock(0);
            if (err != 0) {
                core->reg.pc += 2;
            }
        }

        uint32 new_addrs = coverage_count - before;
        if (new_addrs > 10) {
            printf("  [%3u] 0x%08X: +%u new (total %u, %d clocks)\n",
                   entry_idx, entry, new_addrs, coverage_count, clocks);
        }
        total_new += new_addrs;
    }

    printf("\n=== Coverage: %u unique addresses from %u entries ===\n",
           coverage_count, (uint32)NUM_ENTRIES);

    /* Report calibration access — check which cal offsets were read.
     * Cal base = 0x00FD0000, size = 0x10000 (64KB).
     * Key offsets: 0x02D8 (APA speed), 0x06B0 (timer table),
     *              0x67B0/0x69F0/0x9150/0x9390 (LCA params) */
    printf("\nKey calibration offsets:\n");
    uint32 cal_checks[] = {0x02D8, 0x02D4, 0x06B0, 0x06B6, 0x67B0, 0x69F0, 0x9150, 0x9390};
    int ci;
    for (ci = 0; ci < 8; ci++) {
        uint8 val;
        bus_get_data8(0, FORD_CAL_BASE + cal_checks[ci], &val);
        printf("  cal+0x%04X = 0x%02X\n", cal_checks[ci], val);
    }
    printf("\n");

    /* Set final PC to Background task */
    core->reg.pc = 0x010BA50C;
}
