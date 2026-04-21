"""Parse Ford ETIS Runtime .mdx binary format.
Records: FC <u8-len> <utf8> and FD <u16be-len> <utf8>.
Not standard Java serialization; custom Ford format.
"""
import os, re, json, sys
from collections import OrderedDict

def walk_strings(data):
    records = []
    i = 0
    n = len(data)
    while i < n - 3:
        b = data[i]
        if b == 0xFC:
            ln = data[i+1]
            end = i + 2 + ln
            if 1 <= ln <= 250 and end <= n:
                s = data[i+2:end]
                if all(32 <= c < 127 for c in s):
                    records.append((i, s.decode('ascii', 'replace')))
                    i = end; continue
        elif b == 0xFD:
            if i + 3 < n:
                ln = (data[i+1] << 8) | data[i+2]
                end = i + 3 + ln
                if 1 <= ln <= 60000 and end <= n:
                    s = data[i+3:end]
                    if len(s) > 0 and sum(1 for c in s if 32 <= c < 127) / len(s) > 0.8:
                        records.append((i, s.decode('ascii', 'replace')))
                        i = end; continue
        i += 1
    return records


def summarize(path):
    data = open(path, 'rb').read()
    recs = walk_strings(data)
    summary = {
        'file': os.path.basename(path),
        'size': len(data),
        'records': len(recs),
    }
    # Find ECU name (first occurrence of "Power Steering Control Module", "Powertrain Control Module", etc.)
    ecu_candidates = ['Power Steering Control Module', 'Electro Power Assisted Steering',
                      'Powertrain Control Module', 'Transmission Control Module',
                      'Body Control Module', 'Battery Management', 'Restraint Control',
                      'Anti-Lock Brake', 'ABS Control', 'Instrument Cluster',
                      'Climate Control', 'HVAC', 'Occupant Classification',
                      'Rollover Sensor', 'Steering Column Control', 'Seat Control',
                      'Accessory Protocol Interface', 'Body Gateway', 'Gateway',
                      'Headlamp', 'Tail Lamp', 'Door', 'Door Control',
                      'Image Processing', 'Camera', 'Radar', 'Park Assist',
                      'Cruise Control', 'Audio Control', 'Navigation',
                      'Electric Power Steering', 'Audio Interface',
                      'Adaptive Cruise', 'Steering Angle Sensor',
                      'Transfer Case', 'Brake System', 'Electric Brake',
                      'Vehicle Security', 'Telematics', 'SYNC',
                      'Fuel Pump', 'Fuel Tank', 'Cooling Fan',
                      'Tire Pressure', 'Air Suspension', 'Trailer',
                      'Rear Window Defroster', 'Wiper', 'Washer',
                      'Electric Parking Brake']
    ecu_found = None
    for rec_off, s in recs:
        for c in ecu_candidates:
            if c in s and len(s) < 80:
                ecu_found = s.strip()
                break
        if ecu_found: break
    summary['ecu_name'] = ecu_found

    # Extract DID ID→name map: did_XXXX followed by its human-readable name
    did_map = OrderedDict()
    for i, (off, s) in enumerate(recs):
        m = re.fullmatch(r'did_([0-9A-Fa-f]{4})', s)
        if m and i + 1 < len(recs):
            did_hex = m.group(1).upper()
            # Next record is usually the display name
            next_off, next_s = recs[i+1]
            if not next_s.startswith('did_') and len(next_s) < 200:
                did_map[did_hex] = next_s
    summary['did_count'] = len(did_map)
    summary['dids'] = did_map

    # Routine map
    rtn_map = OrderedDict()
    for i, (off, s) in enumerate(recs):
        m = re.fullmatch(r'routine_([0-9A-Fa-f]{4})', s)
        if m and i + 1 < len(recs):
            rtn_hex = m.group(1).upper()
            next_off, next_s = recs[i+1]
            if not next_s.startswith('routine_') and len(next_s) < 200:
                rtn_map[rtn_hex] = next_s
    summary['routine_count'] = len(rtn_map)
    summary['routines'] = rtn_map

    # Part numbers near SSDS / SsdsPartNumber markers
    parts = set()
    for off, s in recs:
        m = re.fullmatch(r'(?:DS-?)?([A-Z0-9]{2,5})-([A-Z0-9]{4,6})-([A-Z0-9]{1,5})', s)
        if m:
            parts.add(s)
    summary['part_numbers'] = sorted(parts)

    return summary


if __name__ == '__main__':
    DIR = sys.argv[1] if len(sys.argv) > 1 else '/Users/rossfisher/Downloads/fdrs_mdx_files'
    OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else '/tmp/fdrs_extract'
    os.makedirs(OUT_DIR, exist_ok=True)
    index = []
    for fn in sorted(os.listdir(DIR)):
        if not fn.lower().endswith('.mdx'): continue
        path = os.path.join(DIR, fn)
        try:
            summary = summarize(path)
        except Exception as e:
            summary = {'file': fn, 'error': str(e)}
        # Write per-file JSON
        with open(f"{OUT_DIR}/{fn}.json", 'w') as f:
            json.dump(summary, f, indent=2)
        # Index entry
        index.append({
            'file': fn,
            'size': summary.get('size', 0),
            'ecu_name': summary.get('ecu_name'),
            'did_count': summary.get('did_count', 0),
            'routine_count': summary.get('routine_count', 0),
        })
        print(f"  {fn:>16s}  {summary.get('size', 0):>10,d} B  "
              f"{summary.get('did_count', 0):>4d} DIDs  "
              f"{summary.get('routine_count', 0):>3d} rtns  "
              f"ECU={summary.get('ecu_name', '?')!s:<50s}",
              flush=True)
    with open(f"{OUT_DIR}/_index.json", 'w') as f:
        json.dump(index, f, indent=2)
    print(f"\nSaved {len(index)} file summaries to {OUT_DIR}/")
