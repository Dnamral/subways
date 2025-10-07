# save as fetch_tokyo_subway_stream.py
import json
import gzip
import time
import shutil
from datetime import datetime
from pathlib import Path

import requests
import geopandas as gpd

OUT_DIR = Path("data_tokyo")
ARCHIVE_DIR = OUT_DIR / "archive"
OUT_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Overpass QL:
# - Tokyo prefecture (admin_level=4)
# - subway + light_rail routes (relations), fallback subway ways
# - multiple station tagging patterns
# - recurse to fetch member ways/nodes
query = r"""
[out:json][timeout:180];
area["name:en"="Tokyo"]["admin_level"=4]->.tokyo;

(
  relation["route"="subway"](area.tokyo);
  relation["route"="light_rail"](area.tokyo);
  way["railway"="subway"](area.tokyo);

  node["station"="subway"](area.tokyo);
  node["railway"="station"]["station"="subway"](area.tokyo);
  node["railway"="station"]["subway"="yes"](area.tokyo);
);

out body;
>;
out skel qt;
"""

def archive_existing_outputs():
    """
    Move any existing outputs in OUT_DIR that match known patterns to ARCHIVE_DIR,
    appending their mtime to keep uniqueness.
    """
    patterns = [
        "overpass_raw_tokyo*.json",
        "tokyo_subway_all*.geojson",
        "tokyo_subway_routes*.geojson",
        "tokyo_subway_stations*.geojson",
    ]
    moved = 0
    for pat in patterns:
        for p in OUT_DIR.glob(pat):
            if p.is_file():
                mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y%m%d_%H%M%S")
                archived = ARCHIVE_DIR / f"{p.stem}_{mtime}{p.suffix}"
                shutil.move(str(p), str(archived))
                print(f"📦 Archived {p.name} -> archive/{archived.name}")
                moved += 1
    if moved == 0:
        print("🗂️  No existing outputs to archive.")

def overpass_stream_to_file(query: str,
                            url: str = OVERPASS_URL,
                            out_path: Path = OUT_DIR / "overpass_raw_tokyo.json",
                            chunk_bytes: int = 1 << 20):
    """
    POST Overpass QL and stream (auto-decompressed) JSON bytes to disk with progress.
    Returns (elapsed_seconds, bytes_written).
    """
    start = time.time()
    bytes_written = 0

    with requests.post(url, data={"data": query}, stream=True) as r:
        r.raise_for_status()
        # Ensure transparent gzip decompression by requests
        r.raw.decode_content = True
        total = int(r.headers.get("Content-Length", 0))
        enc = r.headers.get("Content-Encoding", "identity")
        print(f"ℹ️  Content-Encoding: {enc}")

        last_t = start
        last_b = 0

        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_bytes):
                if not chunk:
                    continue
                f.write(chunk)
                bytes_written += len(chunk)

                now = time.time()
                if now - last_t >= 0.5:  # update ~2x/sec
                    speed = (bytes_written - last_b) / max(now - last_t, 1e-9)
                    if total:
                        pct = 100 * bytes_written / total
                        print(f"\r↓ {bytes_written:,}/{total:,} bytes ({pct:5.1f}%) @ {speed/1e6:.2f} MB/s", end="")
                    else:
                        print(f"\r↓ {bytes_written:,} bytes @ {speed/1e6:.2f} MB/s", end="")
                    last_t, last_b = now, bytes_written

    print()  # newline
    return time.time() - start, bytes_written

def load_overpass_json_auto(path: Path):
    """
    Robust loader:
    - auto-detects gzip if present,
    - validates JSON,
    - errors clearly if Overpass returned an error payload.
    """
    with open(path, "rb") as f:
        magic = f.read(2)
        f.seek(0)
        raw = f.read()
    if magic == b"\x1f\x8b":
        try:
            text = gzip.decompress(raw).decode("utf-8", errors="replace")
        except Exception as e:
            raise RuntimeError(f"Failed to gunzip {path}: {e}")
    else:
        text = raw.decode("utf-8", errors="replace")

    try:
        obj = json.loads(text)
    except Exception as e:
        snippet = text[:400].replace("\n", "\\n")
        raise RuntimeError(f"Not valid JSON (first 400 chars): {snippet}\nError: {e}")

    if isinstance(obj, dict) and "elements" not in obj:
        preview = (obj.get("remark") if isinstance(obj, dict) else None) or text[:400]
        preview = preview.replace("\n", "\\n")
        raise RuntimeError(f"Overpass response missing 'elements'. Preview: {preview}")

    return obj

def timed_json_dump(obj, out_path: Path, ensure_ascii: bool = False):
    t0 = time.time()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=ensure_ascii)
    elapsed = time.time() - t0
    size = out_path.stat().st_size
    print(f"💾 Wrote {size:,} bytes to {out_path} in {elapsed:.2f}s")
    return elapsed, size

# --- Pre-run: archive existing outputs, then set timestamped targets ---
archive_existing_outputs()
TS = datetime.now().strftime("%Y%m%d_%H%M%S")

raw_overpass_path = OUT_DIR / f"overpass_raw_tokyo_{TS}.json"
final_all_path    = OUT_DIR / f"tokyo_subway_all_{TS}.geojson"
routes_path       = OUT_DIR / f"tokyo_subway_routes_{TS}.geojson"
stations_path     = OUT_DIR / f"tokyo_subway_stations_{TS}.geojson"

# --- Download ---
print("⏳ Querying Overpass (streaming, auto-decompress)…")
dl_s, dl_bytes = overpass_stream_to_file(query, out_path=raw_overpass_path)
print(f"✅ Downloaded {dl_bytes:,} bytes in {dl_s:.2f}s")
