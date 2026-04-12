"""Suppress all error spam from Athrill source files."""
import re
import sys

base = sys.argv[1] if len(sys.argv) > 1 else '/tmp/athrill-ford/athrill-target'

# 1. mpu.c: search_region, mpu_get_pointer errors
path = f'{base}/athrill/src/device/mpu/mpu.c'
with open(path) as f: c = f.read()
c = re.sub(r'printf\("search_region\(\)[^"]*"[^;]*;', '/* suppressed */', c)
c = re.sub(r'printf\("mpu_get_pointer\(\)[^"]*"[^;]*;', '/* suppressed */', c)
with open(path, 'w') as f: f.write(c)
print(f'  mpu.c: suppressed search/pointer errors')

# 2. cpuemu.c: EXIT for timeout
path = f'{base}/athrill/src/main/cpuemu.c'
with open(path) as f: c = f.read()
c = re.sub(r'printf\("EXIT for timeout[^"]*"[^;]*;', '/* suppressed */', c)
with open(path, 'w') as f: f.write(c)
print(f'  cpuemu.c: suppressed timeout spam')

# 3. elf_section.c: symbol section error
path = f'{base}/athrill/src/lib/dwarf/elf_section.c'
with open(path) as f: c = f.read()
c = c.replace(
    'printf("ERROR: can not found symbol section...\\n");',
    '/* suppressed */'
)
with open(path, 'w') as f: f.write(c)
print(f'  elf_section.c: suppressed symbol error')

# 4. elf_dwarf_line.c: Not found ElfDwarfLine
path = f'{base}/athrill/src/lib/dwarf/elf_dwarf_line.c'
with open(path) as f: c = f.read()
c = re.sub(r'printf\("Not found: ElfDwarfLine[^"]*"[^;]*;', '/* suppressed */', c)
with open(path, 'w') as f: f.write(c)
print(f'  elf_dwarf_line.c: suppressed Not found')

print('Done suppressing spam')
