"""Dump every FC/FD record from each Ford ETIS MDX file as plain text.
Produces one .txt per .mdx with offset + string, suitable for grepping."""
import os, sys
sys.path.insert(0, '/tmp')
from extract_mdx import walk_strings

DIR = '/Users/rossfisher/Downloads/fdrs_mdx_files'
OUT = '/tmp/fdrs_extract/strings'
os.makedirs(OUT, exist_ok=True)

for fn in sorted(os.listdir(DIR)):
    if not fn.lower().endswith('.mdx'): continue
    data = open(os.path.join(DIR, fn), 'rb').read()
    recs = walk_strings(data)
    with open(f'{OUT}/{fn}.txt', 'w') as f:
        f.write(f"# {fn}  size={len(data):,} B  records={len(recs)}\n")
        for off, s in recs:
            f.write(f"0x{off:08x}\t{s}\n")
    print(f"  {fn} -> {len(recs):>6d} records", flush=True)
