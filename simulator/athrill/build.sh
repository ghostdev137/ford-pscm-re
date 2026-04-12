#!/bin/bash
# Build patched Athrill2 for Ford PSCM firmware emulation
set -e

PROJ="/mnt/c/Users/Zorro/Desktop/fwproject"
BUILD="/tmp/athrill-ford"
rm -rf "$BUILD"
mkdir -p "$BUILD"

echo "=== Copying source ==="
cp -r "$PROJ/reference/athrill-target" "$BUILD/athrill-target"
rm -rf "$BUILD/athrill-target/athrill"
cp -r "$PROJ/reference/athrill" "$BUILD/athrill-target/athrill"
cp "$PROJ/tools/v850/emu/athrill/ford_setup.c" "$BUILD/athrill-target/athrill/src/main/ford_setup.c"
cp "$PROJ/tools/v850/emu/athrill/bus_patched.h" "$BUILD/athrill-target/athrill/src/bus/bus.h"

echo "=== Patching source ==="

# 1. loader.c: skip debug symbol errors + load into RAM regions
python3 << 'PYEOF'
path = "/tmp/athrill-ford/athrill-target/athrill/src/device/mpu/loader/loader.c"
with open(path) as f: c = f.read()

# Make debug section loading non-fatal
c = c.replace(
    "\terr = elf_symbol_load(elf_data);\n\tif (err != STD_E_OK) {\n\t\treturn err;\n\t}",
    "\t(void)elf_symbol_load(elf_data);"
)
c = c.replace(
    "\terr = elf_dwarf_line_load(elf_data);\n\tif (err != STD_E_OK) {\n\t\treturn err;\n\t}",
    "\t(void)elf_dwarf_line_load(elf_data);"
)
c = c.replace(
    "\terr = elf_dwarf_abbrev_load(elf_data);\n\tif (err != STD_E_OK) {\n\t\treturn err;\n\t}",
    "\t(void)elf_dwarf_abbrev_load(elf_data);"
)
c = c.replace(
    "\terr = elf_dwarf_info_load(elf_data);\n\tif (err != STD_E_OK) {\n\t\treturn err;\n\t}",
    "\t(void)elf_dwarf_info_load(elf_data);"
)
c = c.replace(
    "\terr = elf_dwarf_loc_load(elf_data);\n\tif (err != STD_E_OK) {\n\t\treturn err;\n\t}",
    "\t(void)elf_dwarf_loc_load(elf_data);"
)

# Load ELF segments into RAM too (not just ROM)
c = c.replace(
    "\t\tptr = mpu_address_get_rom(phdr->p_paddr, phdr->p_filesz);\n\t\tif (ptr == NULL) {\n\t\t\tcontinue;\n\t\t}",
    "\t\tptr = mpu_address_get_rom(phdr->p_paddr, phdr->p_filesz);\n\t\tif (ptr == NULL) {\n\t\t\terr = mpu_get_pointer(CPU_CONFIG_CORE_ID_0, phdr->p_paddr, &ptr);\n\t\t\tif (err != STD_E_OK) continue;\n\t\t}"
)

with open(path, 'w') as f: f.write(c)
print("  loader.c patched")
PYEOF

# 2. main.c: add ford_setup include + call, don't fail on symbol errors
python3 << 'PYEOF'
path = "/tmp/athrill-ford/athrill-target/athrill/src/main/main.c"
with open(path) as f: c = f.read()

# Include ford_setup
c = c.replace(
    '#include "athrill_device.h"',
    '#include "athrill_device.h"\n#include "ford_setup.c"'
)

# Don't fail on ELF symbol loading
c = c.replace(
    "\t\telf_load((uint8*)opt->load_file.buffer, &memmap, &entry_addr);\n\t\tif (cpuemu_symbol_set() != STD_E_OK) {\n\t\t\treturn -1;\n\t\t}",
    "\t\telf_load((uint8*)opt->load_file.buffer, &memmap, &entry_addr);\n\t\t(void)cpuemu_symbol_set();"
)

# Call ford_setup_cpu after entry addr
c = c.replace(
    "\tcpuemu_set_entry_addr(entry_addr);",
    "\tcpuemu_set_entry_addr(entry_addr);\n\tford_setup_cpu();"
)

with open(path, 'w') as f: f.write(c)
print("  main.c patched")
PYEOF

# 3. cpuemu.c: don't exit(1) on CPU exceptions, and don't spam errors
python3 << 'PYEOF'
path = "/tmp/athrill-ford/athrill-target/athrill/src/main/cpuemu.c"
with open(path) as f: c = f.read()

# Replace ALL exit(1) with skip-instruction
import re
# Pattern: printf("CPU...Exception!!\n"...);\n\t\t\tfflush(stdout);\n\t\t\texit(1);
c = re.sub(
    r'printf\("CPU\(pc=0x%x\) Exception!!"[^;]*;\s*\n\s*fflush\(stdout\);\s*\n\s*exit\(1\);',
    '/* PATCHED: skip bad instruction */\n\t\t\tvirtual_cpu.cores[i].core.reg.pc += 2;',
    c
)
# Catch any remaining exit(1)
c = re.sub(r'(\s+)exit\(1\);', r'\1/* exit(1) removed */', c)

with open(path, 'w') as f: f.write(c)
print("  cpuemu.c patched")
PYEOF

# 4. cpu_config.c: suppress decode/exec error prints
python3 << 'PYEOF'
path = "/tmp/athrill-ford/athrill-target/src/cpu/config/cpu_config.c"
with open(path) as f: c = f.read()

c = c.replace('printf("Decode Error\\n");', '/* decode error suppressed */')
c = c.replace(
    'printf("Exec Error code[0]=0x%x code[1]=0x%x type_id=0x%x code_id=%u\\n",',
    '/* exec error suppressed */ if(0) printf("x%x x%x x%x %u\\n",'
)
c = c.replace(
    'printf("Not supported code(%d fmt=%d) Error code[0]=0x%x code[1]=0x%x type_id=0x%x\\n",',
    '/* unsupported error suppressed */ if(0) printf("x%d x%d x%x x%x x%x\\n",'
)

with open(path, 'w') as f: f.write(c)
print("  cpu_config.c patched")
PYEOF

# 5. mpu.c: suppress ROM write errors
python3 << 'PYEOF'
path = "/tmp/athrill-ford/athrill-target/athrill/src/device/mpu/mpu.c"
with open(path) as f: c = f.read()
import re
c = re.sub(r'printf\("mpu_put_data\d+:error:[^"]*"[^;]*;', '/* ROM write error suppressed */', c)
with open(path, 'w') as f: f.write(c)
print("  mpu.c patched")
PYEOF

echo "=== Building ==="
cd "$BUILD/athrill-target"
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release 2>&1 | tail -3
make -j$(nproc) 2>&1 | tail -5

echo ""
echo "=== Build complete ==="
ls -lh "$BUILD/athrill-target/build/athrill2"

# Copy binary back
cp "$BUILD/athrill-target/build/athrill2" "$PROJ/tools/v850/emu/athrill/athrill2"
echo "Copied to tools/v850/emu/athrill/athrill2"
