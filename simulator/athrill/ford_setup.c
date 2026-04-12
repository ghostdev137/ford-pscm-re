/*
 * Ford PSCM firmware setup for Athrill2.
 *
 * Called after ELF loading to set up registers and apply the
 * RAM init table, mimicking what the real SBL does before
 * handing off to the strategy code.
 *
 * This file is #included into a patched main.c.
 */

#include "bus.h"
#include <string.h>

/* Ford PSCM memory map */
#define FORD_CAL_BASE      0x00FD0000
#define FORD_STRATEGY_BASE 0x01000000
#define FORD_RAM_BASE      0x10000000
#define FORD_EP_BASE       0x40010100
#define FORD_SP_INIT       0x4001FF00
#define FORD_CTBP          0x0100220C

/* Init table marker */
#define INIT_MARKER        0x001000EF
#define INIT_TABLE_OFFSET  0x9230  /* offset in block0 */

/* Register indices */
#define REG_SP  3
#define REG_GP  4
#define REG_EP  30
#define REG_LP  31

/* AUTOSAR task entry points (from descriptor table analysis) */
#define ENTRY_BACKGROUND   0x010BA50C
#define ENTRY_COM          0x010BC360
#define ENTRY_FORDQM       0x010DA378
#define ENTRY_FORDASIL     0x010CD53C

/* System register IDs */
#define SYSREG_CTBP  20

/* Read a big-endian uint32 from bus memory */
static uint32 ford_read_be32(uint32 addr)
{
    uint8 b[4];
    bus_get_data8(0, addr + 0, &b[0]);
    bus_get_data8(0, addr + 1, &b[1]);
    bus_get_data8(0, addr + 2, &b[2]);
    bus_get_data8(0, addr + 3, &b[3]);
    return ((uint32)b[0] << 24) | ((uint32)b[1] << 16) |
           ((uint32)b[2] << 8)  | (uint32)b[3];
}

static void ford_apply_init_table(void)
{
    /*
     * The init table at block0+0x9230 has 16-byte entries:
     *   [marker:4] [ram_end:4] [ram_start:4] [ctrl:4]
     * All big-endian. Marker = 0x001000EF.
     *
     * ctrl high byte:
     *   0xA0 = zero-fill RAM [ram_start..ram_end]
     *   0x01 = ROM-to-RAM copy, source = ctrl & 0x00FFFFFF
     */
    uint32 offset = FORD_STRATEGY_BASE + INIT_TABLE_OFFSET;
    int count = 0;
    uint32 total_bytes = 0;

    while (count < 100) {
        uint32 marker = ford_read_be32(offset);
        if (marker != INIT_MARKER) break;

        uint32 ram_end   = ford_read_be32(offset + 4);
        uint32 ram_start = ford_read_be32(offset + 8);
        uint32 ctrl      = ford_read_be32(offset + 12);

        if (ram_end < ram_start) {
            offset += 16;
            count++;
            continue;
        }

        uint32 size = ram_end - ram_start + 1;
        uint8 op = (ctrl >> 24) & 0xFF;

        if ((op & 0xF0) == 0xA0) {
            /* Zero-fill */
            uint32 addr;
            for (addr = ram_start; addr <= ram_end; addr++) {
                bus_put_data8(0, addr, 0x00);
            }
            printf("  init[%2d]: zero  0x%08X-0x%08X (%5u B)\n",
                   count, ram_start, ram_end, size);
        }
        else if (op == 0x01) {
            /* ROM-to-RAM copy */
            uint32 rom_src = ctrl & 0x00FFFFFF;
            /* The source address is typically in the strategy block */
            if (rom_src < 0x01000000) {
                rom_src += FORD_STRATEGY_BASE;
            }
            uint32 i;
            for (i = 0; i < size; i++) {
                uint8 byte;
                bus_get_data8(0, rom_src + i, &byte);
                bus_put_data8(0, ram_start + i, byte);
            }
            printf("  init[%2d]: copy  0x%08X-0x%08X <- 0x%08X (%5u B)\n",
                   count, ram_start, ram_end, rom_src, size);
        }
        else {
            printf("  init[%2d]: skip  0x%08X-0x%08X ctrl=0x%08X\n",
                   count, ram_start, ram_end, ctrl);
        }

        total_bytes += size;
        offset += 16;
        count++;
    }
    printf("Ford: processed %d init table entries (%u bytes total)\n",
           count, total_bytes);
}

static void ford_prefill_ep_area(void)
{
    /*
     * Pre-fill the EP-relative area (0x40010100-0x40010200) with 0x01.
     * This fakes "BSW initialized" flags that AUTOSAR tasks check
     * via EP-relative loads (SLD.B/SLD.W). Without this, tasks
     * loop forever waiting for BSW modules to report ready.
     */
    uint32 addr;
    for (addr = FORD_EP_BASE; addr < FORD_EP_BASE + 0x200; addr++) {
        bus_put_data8(0, addr, 0x01);
    }
    printf("Ford: pre-filled EP area 0x%08X-0x%08X with 0x01\n",
           FORD_EP_BASE, FORD_EP_BASE + 0x200);
}

static void ford_setup_cpu(void)
{
    extern CpuType virtual_cpu;
    TargetCoreType *core = &virtual_cpu.cores[0].core;

    printf("\n=== Ford PSCM V850E2M Setup ===\n");

    /* Full register setup — replicate what the boot ROM does */
    core->reg.r[REG_SP] = FORD_SP_INIT;
    core->reg.r[REG_GP] = FORD_CAL_BASE;
    core->reg.r[REG_EP] = FORD_EP_BASE;
    core->reg.r[REG_LP] = 0;

    /* Set CTBP system register */
    core->reg.sys.grp[0][0].r[SYSREG_CTBP] = FORD_CTBP;

    /* PSW: interrupts disabled, supervisor mode */
    core->reg.sys.grp[0][0].r[5] = 0x20;

    printf("  SP   = 0x%08X\n", FORD_SP_INIT);
    printf("  GP   = 0x%08X (calibration base)\n", FORD_CAL_BASE);
    printf("  EP   = 0x%08X\n", FORD_EP_BASE);
    printf("  CTBP = 0x%08X\n", FORD_CTBP);

    /* Stub internal ROM calls — write JMP [r13] (return) at addresses
     * the SBL calls into. This lets the SBL continue past ROM calls. */
    /* JMP [reg1] encoding: hw0 = 00000_000000_RRRRR, R=reg1 */
    /* r13 = 0x0D: hw0 = 0x000D → bytes 0D 00 */
    /* Stub internal ROM calls with JMP [lp] returns */
    /* JMP [r13]: hw=0x006D. Also stub nearby addresses. */
    uint32 stub_addr;
    for (stub_addr = 0xFFF20000; stub_addr < 0xFFF20200; stub_addr += 2) {
        bus_put_data8(0, stub_addr, 0x6D);  /* JMP [r13] */
        bus_put_data8(0, stub_addr + 1, 0x00);
    }
    printf("  ROM stubs: JMP [r13] at 0xFFF20000-0xFFF20200\n");

    /* Fill unwritten flash areas with 0xFF (erased flash state).
     * The ELF only loaded SBL (2KB) at addr 0, rest of 64KB ROM is 0.
     * Real flash has 0xFF in unwritten areas. We must write via mpu_get_pointer
     * since bus_put won't write to ROM. */
    {
        uint8 *rom_ptr = NULL;
        extern Std_ReturnType mpu_get_pointer(CoreIdType core_id, uint32 addr, uint8 **data);
        if (mpu_get_pointer(0, 0x00000800, &rom_ptr) == 0 && rom_ptr != NULL) {
            memset(rom_ptr, 0xFF, 0x10000 - 0x800);  /* Fill 0x800-0xFFFF with 0xFF */
            printf("  Flash area 0x800-0xFFFF filled with 0xFF (erased state)\n");
        }
    }

    /* Apply RAM init table (zero-fill + ROM-to-RAM copy) */
    ford_apply_init_table();

    /* Pre-fill EP area to fake BSW init flags */
    ford_prefill_ep_area();

    /* PC is set by DEBUG_FUNC_RESET_PC in device config — don't override */
    printf("  PC   = 0x%08X (from device config)\n", core->reg.pc);

    /* Enable cal access logging */
    {
        extern int cal_log_enabled;
        extern uint32 cal_log_count;
        cal_log_count = 0;
        cal_log_enabled = 1;
    }

    /* Fill EP area with 0x01 for BSW init checks */
    {
        uint32 a;
        for (a = FORD_EP_BASE; a < FORD_EP_BASE + 0x400; a++)
            bus_put_data8(0, a, 0x01);
        for (a = 0x40010000; a < 0x40026000; a++)
            bus_put_data8(0, a, 0x01);
    }

    printf("=== Setup complete (cal logging ON) ===\n\n");
}

static void ford_print_cal_log(void) {
    extern uint32 cal_log_pc[];
    extern uint32 cal_log_addr[];
    extern uint32 cal_log_count;
    if (cal_log_count == 0) return;
    printf("\n=== Cal Access Log: %u reads ===\n", cal_log_count);
    uint32 i, printed = 0;
    for (i = 0; i < cal_log_count && printed < 300; i++) {
        uint32 cal_off = cal_log_addr[i] - 0x00FD0000u;
        printf("  PC=0x%08X cal+0x%04X\n", cal_log_pc[i], cal_off);
        printed++;
    }
}

static void ford_atexit_handler(void) { ford_print_cal_log(); }
