#!/usr/bin/env python3

import sys
from pathlib import Path
from binaryninja.warp import *

def process_binary(input_file: str, output_dir: str) -> None:
    input_path = Path(input_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{input_path.stem}.warp"
    processor = WarpProcessor()
    processor.add_path(input_file)
    file = processor.start()
    if not file:
        return
    buffer = file.to_data_buffer()
    with open(output_file, 'wb') as f:
        f.write(bytes(buffer))
    print(f"Wrote {len(buffer)} bytes to {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_binary> <output_directory>")
        sys.exit(1)
    binaryninja._init_plugins()
    process_binary(sys.argv[1], sys.argv[2])