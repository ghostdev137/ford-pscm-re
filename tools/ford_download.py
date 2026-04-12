#!/usr/bin/env python3
"""
Download Ford PSCM firmware from FDSP (Ford Diagnostic Service Platform).

Extracts download URLs from FDRS application manifests and downloads VBF files.
Requires FDRS to be installed and have cached manifests for the target VIN.

Usage:
    python ford_download.py [--list] [--download PART_NUMBER] [--all]
"""

import base64, json, os, re, sys, urllib.request, ssl

MANIFEST_DIR = r"C:\ProgramData\Ford Motor Company\FDRS\fdrs\data\application_manifest"
OUTPUT_DIR = r"C:\Users\Zorro\Desktop\fwproject\firmware\downloads"
BASE_URL = "https://www.fdspcl.dealerconnection.com/FdspProviderWeb/Proxy/BinaryDownloadProxy"


def find_all_downloads():
    """Extract all firmware download URLs from FDRS manifests."""
    downloads = {}

    for root, dirs, files in os.walk(MANIFEST_DIR):
        for f in files:
            if not f.endswith('.json'):
                continue
            path = os.path.join(root, f)
            with open(path) as fh:
                raw = fh.read()

            vin = f.split('_')[0]
            if 'XXXX' in vin:
                continue

            # Find all software entries with URLs
            # Pattern: "id":"PART-NUM","type":"TYPE",...,"url":"https://...BinaryDownloadProxy?value=BASE64"
            pattern = r'"id":"([^"]+)","type":"([^"]+)"[^}]*?"url":"https://www\.fdspcl\.dealerconnection\.com/FdspProviderWeb/Proxy/BinaryDownloadProxy\?value=([A-Za-z0-9+/=]+)"'

            for match in re.finditer(pattern, raw):
                part_id = match.group(1)
                sw_type = match.group(2)
                b64 = match.group(3)
                decoded = base64.b64decode(b64).decode('ascii')

                # Parse decoded params
                params = dict(p.split('=', 1) for p in decoded.split('&'))
                keyname = params.get('keyname', '')
                filesig = params.get('filesignature', '')

                full_url = f"{BASE_URL}?value={b64}"

                if part_id not in downloads:
                    downloads[part_id] = {
                        'type': sw_type,
                        'vin': vin,
                        'keyname': keyname,
                        'filesig': filesig,
                        'url': full_url,
                        'b64': b64,
                    }

    return downloads


def try_download(url, output_path):
    """Attempt to download a file from the given URL."""
    # Try without auth first (some files may be publicly accessible)
    ctx = ssl.create_default_context()

    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'FDRS/1.0')

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            data = resp.read()
            with open(output_path, 'wb') as f:
                f.write(data)
            return len(data), resp.status
    except urllib.error.HTTPError as e:
        return 0, e.code
    except Exception as e:
        return 0, str(e)


def main():
    downloads = find_all_downloads()

    if '--list' in sys.argv or len(sys.argv) == 1:
        print(f"Found {len(downloads)} firmware files in FDRS manifests:\n")
        for part_id in sorted(downloads.keys()):
            d = downloads[part_id]
            print(f"  {part_id:22s} {d['type']:25s} VIN={d['vin']}  key={d['keyname'][:40]}")
        print(f"\nTo download: python ford_download.py --download <PART_NUMBER>")
        print(f"To try all:  python ford_download.py --all")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    targets = []
    if '--all' in sys.argv:
        targets = list(downloads.keys())
    elif '--download' in sys.argv:
        idx = sys.argv.index('--download')
        if idx + 1 < len(sys.argv):
            pn = sys.argv[idx + 1]
            if pn in downloads:
                targets = [pn]
            else:
                print(f"Part number {pn} not found. Use --list to see available.")
                return

    for part_id in targets:
        d = downloads[part_id]
        output = os.path.join(OUTPUT_DIR, f"{part_id}.VBF")
        print(f"Downloading {part_id} ({d['type']})...")
        print(f"  URL: {d['url'][:100]}...")

        size, status = try_download(d['url'], output)

        if size > 0:
            print(f"  OK: {size:,} bytes -> {output}")
        else:
            print(f"  FAILED: status={status}")
            # Try constructing the direct URL with the part number
            alt_b64 = base64.b64encode(
                f"keyname={part_id}.VBF&filetype=binary&environment=PROD".encode()
            ).decode()
            alt_url = f"{BASE_URL}?value={alt_b64}"
            print(f"  Trying alternate URL...")
            size2, status2 = try_download(alt_url, output)
            if size2 > 0:
                print(f"  OK (alt): {size2:,} bytes -> {output}")
            else:
                print(f"  FAILED (alt): status={status2}")


if __name__ == '__main__':
    main()
