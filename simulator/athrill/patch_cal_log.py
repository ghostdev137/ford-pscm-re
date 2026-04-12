"""Add calibration access logging to Athrill's bus.h and ford_setup.c"""
import sys

base = sys.argv[1] if len(sys.argv) > 1 else '/tmp/athrill-ford/athrill-target'

# 1. Patch bus.h to log cal reads
path = f'{base}/athrill/src/bus/bus.h'
with open(path) as f:
    c = f.read()

cal_log = '''
/* Cal access logging */
#define CAL_BASE 0x00FD0000u
#define CAL_SIZE 0x00010000u
#define CAL_LOG_SIZE 8192
static uint32 cal_log_pc[CAL_LOG_SIZE];
static uint32 cal_log_addr[CAL_LOG_SIZE];
static uint32 cal_log_count = 0;
static int cal_log_enabled = 0;

static inline void cal_log_access(uint32 addr) {
    if (cal_log_enabled && addr >= CAL_BASE && addr < CAL_BASE + CAL_SIZE) {
        if (cal_log_count < CAL_LOG_SIZE) {
            extern CpuType virtual_cpu;
            cal_log_pc[cal_log_count] = virtual_cpu.cores[0].core.reg.pc;
            cal_log_addr[cal_log_count] = addr;
            cal_log_count++;
        }
    }
}
'''

if 'cal_log_access' not in c:
    c = c.replace('#ifdef DISABLE_BUS_ACCESS_LOG',
                   cal_log + '\n#ifdef DISABLE_BUS_ACCESS_LOG')

    # Add cal_log_access to each bus_get function
    for sz in ['8', '16', '32']:
        old = f'static inline Std_ReturnType bus_get_data{sz}(CoreIdType core_id, uint32 addr, uint{sz} *data)\n{{\n\tStd_ReturnType err = mpu_get_data{sz}(core_id, addr, data);'
        new = f'static inline Std_ReturnType bus_get_data{sz}(CoreIdType core_id, uint32 addr, uint{sz} *data)\n{{\n\tcal_log_access(addr);\n\tStd_ReturnType err = mpu_get_data{sz}(core_id, addr, data);'
        c = c.replace(old, new)

    with open(path, 'w') as f:
        f.write(c)
    print(f'  bus.h: added cal_log_access')
else:
    print(f'  bus.h: already patched')

# 2. Add cal log printing to ford_setup.c
path = f'{base}/athrill/src/main/ford_setup.c'
with open(path) as f:
    c = f.read()

if 'ford_print_cal_log' not in c:
    cal_print = '''
static void ford_print_cal_log(void) {
    extern uint32 cal_log_pc[];
    extern uint32 cal_log_addr[];
    extern uint32 cal_log_count;

    if (cal_log_count == 0) return;

    printf("\\n=== Cal Access Log: %u reads ===\\n", cal_log_count);
    uint32 i, printed = 0;
    uint32 last_addr = 0xFFFFFFFF;
    for (i = 0; i < cal_log_count && printed < 200; i++) {
        if (cal_log_addr[i] != last_addr) {
            uint32 cal_off = cal_log_addr[i] - 0x00FD0000u;
            printf("  PC=0x%08X cal+0x%04X\\n", cal_log_pc[i], cal_off);
            last_addr = cal_log_addr[i];
            printed++;
        }
    }
}
'''
    # Insert before ford_setup_cpu
    c = c.replace('static void ford_setup_cpu(void)',
                   cal_print + '\nstatic void ford_setup_cpu(void)')

    # Enable cal logging and print at end
    c = c.replace(
        '    printf("=== Setup complete ===\\n\\n");',
        '    cal_log_enabled = 1;\n'
        '    printf("=== Setup complete (cal logging ON) ===\\n\\n");'
    )

    with open(path, 'w') as f:
        f.write(c)
    print(f'  ford_setup.c: added cal log print')
else:
    print(f'  ford_setup.c: already patched')

print('Done')
