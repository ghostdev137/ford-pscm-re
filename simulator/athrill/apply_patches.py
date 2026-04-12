"""Apply all Athrill patches for Ford PSCM emulation."""
import re, os, sys

base = sys.argv[1] if len(sys.argv) > 1 else '.'

def read(p): return open(os.path.join(base, p)).read()
def write(p, c): open(os.path.join(base, p), 'w').write(c)

# loader.c
p = 'athrill/src/device/mpu/loader/loader.c'
c = read(p)
for fn in ['elf_symbol_load','elf_dwarf_line_load','elf_dwarf_abbrev_load','elf_dwarf_info_load','elf_dwarf_loc_load']:
    c = c.replace(f'\terr = {fn}(elf_data);\n\tif (err != STD_E_OK) {{\n\t\treturn err;\n\t}}', f'\t(void){fn}(elf_data);')
c = c.replace(
    '\t\tptr = mpu_address_get_rom(phdr->p_paddr, phdr->p_filesz);\n\t\tif (ptr == NULL) {\n\t\t\tcontinue;\n\t\t}',
    '\t\tptr = mpu_address_get_rom(phdr->p_paddr, phdr->p_filesz);\n\t\tif (ptr == NULL) {\n\t\t\terr = mpu_get_pointer(CPU_CONFIG_CORE_ID_0, phdr->p_paddr, &ptr);\n\t\t\tif (err != STD_E_OK) continue;\n\t\t}')
write(p, c); print('loader OK')

# main.c
p = 'athrill/src/main/main.c'
c = read(p)
if 'ford_setup.c' not in c:
    c = c.replace('#include "athrill_device.h"', '#include "athrill_device.h"\n#include "ford_setup.c"')
c = c.replace(
    '\t\telf_load((uint8*)opt->load_file.buffer, &memmap, &entry_addr);\n\t\tif (cpuemu_symbol_set() != STD_E_OK) {\n\t\t\treturn -1;\n\t\t}',
    '\t\telf_load((uint8*)opt->load_file.buffer, &memmap, &entry_addr);\n\t\t(void)cpuemu_symbol_set();')
if 'ford_setup_cpu' not in c:
    c = c.replace('\t\tcpuemu_init(cpuemu_thread_run, opt);\n\t\tdo_cui();',
        '\t\tcpuemu_init(cpuemu_thread_run, opt);\n\t\tford_setup_cpu();\n\t\tdo_cui();')
    c = c.replace('\t\tcpuemu_init(NULL, opt);\n\t\tcpuemu_set_cpu_end_clock',
        '\t\tcpuemu_init(NULL, opt);\n\t\tford_setup_cpu();\n\t\tcpuemu_set_cpu_end_clock')
write(p, c); print('main OK')

# cpuemu.c
p = 'athrill/src/main/cpuemu.c'
lines = read(p).split('\n')
new = []; skip = 0
for i, line in enumerate(lines):
    if skip > 0: skip -= 1; continue
    if 'Exception!!' in line:
        new.append('\t\t\tvirtual_cpu.cores[i].core.reg.pc += 2;')
        j = i + 1
        while j < len(lines) and j < i + 4:
            if 'fflush' in lines[j] or 'exit(1)' in lines[j]: skip += 1
            else: break
            j += 1
        continue
    new.append(line)
c = '\n'.join(new)
c = re.sub(r'(\s+)exit\(1\);', r'\1/* removed */', c)
c = re.sub(r'printf\("EXIT for timeout[^"]*"[^;]*;', '/* suppressed */', c)
write(p, c); print('cpuemu OK')

# cpu_config.c
p = 'src/cpu/config/cpu_config.c'
c = read(p)
c = re.sub(r'(\t+)printf\("[^"]*[Ee]rror[^"]*"[^;]*;', r'\1/* suppressed */', c)
c = re.sub(r'(\t+)printf\("[^"]*[Dd]ecode[^"]*"[^;]*;', r'\1/* suppressed */', c)
if 'cal_current_pc' not in c:
    c = c.replace('Std_ReturnType cpu_supply_clock(CoreIdType core_id)\n{',
        'extern uint32 cal_current_pc;\nStd_ReturnType cpu_supply_clock(CoreIdType core_id)\n{')
    c = c.replace('\tvirtual_cpu.cores[core_id].core.reg.r[0] = 0U;',
        '\tvirtual_cpu.cores[core_id].core.reg.r[0] = 0U;\n\t{extern uint32 cal_current_pc; cal_current_pc = virtual_cpu.cores[core_id].core.reg.pc;}', 1)
write(p, c); print('cpu_config OK')

# bus.c
p = 'athrill/src/bus/bus.c'
c = read(p)
if 'cal_log_pc' not in c:
    c += '\n#include "std_types.h"\nuint32 cal_log_pc[8192];\nuint32 cal_log_addr[8192];\nuint32 cal_log_count = 0;\nint cal_log_enabled = 0;\nuint32 cal_current_pc = 0;\n'
    write(p, c)
print('bus OK')

# mpu.c
p = 'athrill/src/device/mpu/mpu.c'
c = read(p)
c = re.sub(r'\tprintf\([^;]*;', '\t/* suppressed */', c)
write(p, c); print('mpu OK')

# dwarf files
for p in ['athrill/src/lib/dwarf/elf_section.c', 'athrill/src/lib/dwarf/elf_dwarf_line.c']:
    fp = os.path.join(base, p)
    if os.path.exists(fp):
        c = open(fp).read()
        c = re.sub(r'printf\("[^"]*symbol[^"]*"[^;]*;', '/* suppressed */', c)
        c = re.sub(r'printf\("Not found[^"]*"[^;]*;', '/* suppressed */', c)
        open(fp, 'w').write(c)
print('dwarf OK')

print('\nAll patches applied!')
