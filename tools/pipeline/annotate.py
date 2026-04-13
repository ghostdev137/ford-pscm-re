#!/usr/bin/env python3
"""Send each decompile to GLM-4.7-Flash, ask for JSON-formatted annotations."""
import json, os, sys, time, concurrent.futures, traceback
from openai import OpenAI

DECOMP_DIR = "/tmp/pscm/decompiles_clean"
OUT_PATH = "/tmp/pscm/annotations.json"
ENDPOINT = "http://100.69.219.3:8000/v1"
MODEL = "glm-4.7-flash"
PARALLEL = 8

PROMPT = """You are reverse-engineering Ford Transit PSCM (Power Steering Control Module) firmware on Renesas RH850.
The function below was decompiled by Ghidra. V850 register notes: ep is element-pointer (struct base), CTBP is call-table base, gp is calibration base.

Output ONLY a single JSON object with these keys (no markdown, no commentary, no code fences):
{
  "name": "<short snake_case function name guess; if uncertain prefix with 'maybe_'>",
  "purpose": "<one-line guess at function purpose>",
  "vars": {{ "<old_name>": "<new_name>", ... }},
  "struct_fields": [["<offset_hex>", "<type>", "<field_name>"], ...]
}

Decompile:
```c
{code}
```"""

def annotate(addr, code):
    c = OpenAI(base_url=ENDPOINT, api_key="x")
    prompt = PROMPT.replace("{code}", code)
    try:
        r = c.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500,
        )
        txt = r.choices[0].message.content.strip()
        # try to extract JSON if model wrapped it
        if txt.startswith("```"):
            txt = txt.split("```", 2)[1]
            if txt.startswith("json"): txt = txt[4:]
            txt = txt.strip()
        ann = json.loads(txt)
        return addr, ann, None
    except Exception as e:
        return addr, None, f"{type(e).__name__}: {e}"

def main():
    files = sorted(os.listdir(DECOMP_DIR))
    print(f"annotating {len(files)} functions, parallel={PARALLEL}")
    out = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as f: out = json.load(f)
        print(f"resuming from {len(out)} cached annotations")

    pending = [f for f in files if f[:-2] not in out]
    print(f"{len(pending)} pending")

    started = time.time()
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL) as ex:
        futures = {}
        for fname in pending:
            addr = fname[:-2]
            with open(os.path.join(DECOMP_DIR, fname)) as f: code = f.read()
            futures[ex.submit(annotate, addr, code)] = addr
        for fut in concurrent.futures.as_completed(futures):
            addr, ann, err = fut.result()
            done += 1
            if err:
                print(f"  [{done}/{len(pending)}] {addr}: ERR {err[:80]}")
            else:
                out[addr] = ann
                if done % 10 == 0:
                    elapsed = time.time() - started
                    rate = done / elapsed if elapsed else 0
                    eta = (len(pending) - done) / rate if rate else 0
                    print(f"  [{done}/{len(pending)}] {addr}: {ann.get('name','?')[:30]}  ({rate:.1f}/s, eta {eta:.0f}s)")
                    with open(OUT_PATH, "w") as f: json.dump(out, f, indent=2)
    with open(OUT_PATH, "w") as f: json.dump(out, f, indent=2)
    print(f"done. {len(out)} annotations saved to {OUT_PATH}")

if __name__ == "__main__":
    main()
