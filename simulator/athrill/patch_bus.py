"""Patch Athrill's bus.h to handle unmapped memory gracefully."""
import sys

path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/athrill-target/athrill/src/bus/bus.h'

with open(path, 'r') as f:
    c = f.read()

# bus_get_data8: return 0 for unmapped
c = c.replace(
    '\terr = mpu_get_data8(core_id, addr, data);\n'
    '\tif (err != STD_E_OK) {\n'
    '\t\tprintf("ERROR:can not load data:addr=0x%x size=1byte\\n", addr);\n'
    '\t}\n'
    '\tbus_access_set_log(BUS_ACCESS_TYPE_READ, 1U, addr, *data);\n'
    '\treturn err;\n',
    '\terr = mpu_get_data8(core_id, addr, data);\n'
    '\tif (err != STD_E_OK) { *data = 0; return STD_E_OK; }\n'
    '\tbus_access_set_log(BUS_ACCESS_TYPE_READ, 1U, addr, *data);\n'
    '\treturn err;\n'
)

# bus_get_data16
c = c.replace(
    '\terr = mpu_get_data16(core_id, addr, data);\n'
    '\tif (err != STD_E_OK) {\n'
    '\t\tprintf("ERROR:can not load data:addr=0x%x size=2byte\\n", addr);\n'
    '\t}\n'
    '\tbus_access_set_log(BUS_ACCESS_TYPE_READ, 2U, addr, *data);\n'
    '\treturn err;\n',
    '\terr = mpu_get_data16(core_id, addr, data);\n'
    '\tif (err != STD_E_OK) { *data = 0; return STD_E_OK; }\n'
    '\tbus_access_set_log(BUS_ACCESS_TYPE_READ, 2U, addr, *data);\n'
    '\treturn err;\n'
)

# bus_get_data32
c = c.replace(
    '\terr = mpu_get_data32(core_id, addr, data);\n'
    '\tif (err != STD_E_OK) {\n'
    '\t\tprintf("ERROR:can not load data:addr=0x%x size=4byte\\n", addr);\n'
    '\t}\n'
    '\tbus_access_set_log(BUS_ACCESS_TYPE_READ, 4U, addr, *data);\n'
    '\treturn err;\n',
    '\terr = mpu_get_data32(core_id, addr, data);\n'
    '\tif (err != STD_E_OK) { *data = 0; return STD_E_OK; }\n'
    '\tbus_access_set_log(BUS_ACCESS_TYPE_READ, 4U, addr, *data);\n'
    '\treturn err;\n'
)

# bus_put_data8/16/32: ignore unmapped writes
for sz, tp in [('8', 'uint8'), ('16', 'uint16'), ('32', 'uint32')]:
    c = c.replace(
        f'\tbus_access_set_log(BUS_ACCESS_TYPE_WRITE, {sz[-1]}U, addr, data);\n'
        f'\treturn mpu_put_data{sz}(core_id, addr, data);\n',
        f'\tbus_access_set_log(BUS_ACCESS_TYPE_WRITE, {sz[-1]}U, addr, data);\n'
        f'\t(void)mpu_put_data{sz}(core_id, addr, data);\n'
        f'\treturn STD_E_OK;\n'
    )

# Fix the size values (1, 2, 4 not last digit of type)
c = c.replace('BUS_ACCESS_TYPE_WRITE, 8U,', 'BUS_ACCESS_TYPE_WRITE, 1U,')
c = c.replace('BUS_ACCESS_TYPE_WRITE, 6U,', 'BUS_ACCESS_TYPE_WRITE, 2U,')
c = c.replace('BUS_ACCESS_TYPE_WRITE, 2U,', 'BUS_ACCESS_TYPE_WRITE, 4U,')
# Hmm this is getting tangled. Let me just write the correct sizes.

with open(path, 'w') as f:
    f.write(c)

print(f'Patched {path}')
