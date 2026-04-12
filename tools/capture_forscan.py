"""
mitmproxy addon to capture FORScan firmware downloads.

Run:
    mitmdump -s capture_forscan.py -p 8888 --set ssl_insecure=true

Then configure FORScan to use proxy localhost:8888:
    1. Open FORScan settings.ini
    2. Or set system proxy: netsh winhttp set proxy proxy-server="http=localhost:8888;https=localhost:8888"
    3. Run FORScan and trigger firmware download

All captured files saved to ./captured/
All URLs logged to ./captured/urls.log
"""

import os
import mitmproxy.http

SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "firmware", "captured")
os.makedirs(SAVE_DIR, exist_ok=True)

LOG_PATH = os.path.join(SAVE_DIR, "urls.log")


class FordCapture:
    def response(self, flow: mitmproxy.http.HTTPFlow):
        url = flow.request.pretty_url
        status = flow.response.status_code
        content_len = len(flow.response.content) if flow.response.content else 0
        content_type = flow.response.headers.get("content-type", "")

        # Log everything
        with open(LOG_PATH, "a") as f:
            f.write(f"{flow.request.method} {url} -> {status} ({content_len} bytes, {content_type})\n")
            for k, v in flow.request.headers.items():
                f.write(f"  REQ {k}: {v}\n")
            f.write("\n")

        # Print interesting requests
        is_ford = "ford" in url.lower() or "fdsp" in url.lower() or "dealerconnect" in url.lower()
        is_binary = content_len > 1000 and ("binary" in content_type or "octet" in content_type or "zip" in content_type or "application/vbf" in content_type)
        is_vbf = ".vbf" in url.lower() or ".zip" in url.lower() or "BinaryDownload" in url

        if is_ford or is_binary or is_vbf:
            print(f"\n{'='*60}")
            print(f"[FORD] {flow.request.method} {url}")
            print(f"  Status: {status}, Size: {content_len:,} bytes")
            print(f"  Content-Type: {content_type}")

            # Save response body
            if flow.response.content and content_len > 100:
                # Determine filename
                fname = None
                cd = flow.response.headers.get("content-disposition", "")
                if "filename=" in cd:
                    fname = cd.split("filename=")[-1].strip('" ')

                if not fname:
                    # Try to extract from URL
                    if "BinaryDownload" in url:
                        import base64, urllib.parse
                        parsed = urllib.parse.urlparse(url)
                        params = urllib.parse.parse_qs(parsed.query)
                        if "value" in params:
                            try:
                                decoded = base64.b64decode(params["value"][0]).decode()
                                kv = dict(p.split("=", 1) for p in decoded.split("&"))
                                fname = kv.get("keyname", "unknown.bin")
                            except:
                                pass

                if not fname:
                    fname = f"response_{status}_{content_len}.bin"

                save_path = os.path.join(SAVE_DIR, fname)
                with open(save_path, "wb") as f:
                    f.write(flow.response.content)
                print(f"  SAVED: {save_path}")

            # Log auth headers
            auth = flow.request.headers.get("authorization", "")
            cookie = flow.request.headers.get("cookie", "")
            if auth:
                print(f"  AUTH: {auth[:80]}...")
            if cookie:
                print(f"  COOKIE: {cookie[:80]}...")


addons = [FordCapture()]
