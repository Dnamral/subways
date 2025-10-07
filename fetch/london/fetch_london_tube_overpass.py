# save as fetch_london_tube_overpass.py
import time, requests, json
from pathlib import Path
from datetime import datetime

OUT = Path("../data/london"); OUT.mkdir(parents=True, exist_ok=True)

MIRRORS = [
    "https://overpass.kumi.systems/api/interpreter",   # often fastest
    "https://overpass-api.de/api/interpreter",          # main
]

# Greater London bbox: south, west, north, east
BBOX = (51.2868, -0.5103, 51.6919, 0.3340)

Q_IDS = f"""
[out:json][timeout:120];
relation["route"="subway"]["network"="London Underground"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
out ids;
"""

# Greater London bbox (S, W, N, E) — you already have BBOX
STATIONS_Q = f"""
[out:json][timeout:120];
(
  node["station"="subway"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
  node["railway"="station"]["subway"="yes"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
);
out body;
"""

def q_members(ids, batch_size=200):
    chunks = []
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        id_list = ",".join(str(x) for x in batch)
        chunks.append(f"  relation(id:{id_list});")
    body = "\n".join(chunks)
    return f"""[out:json][timeout:240];
(
{body}
);
out body;
>;
out skel qt;
"""

def human(n):
    for u in ("B","KB","MB","GB","TB"):
        if n < 1024 or u == "TB": return f"{n:.2f} {u}"
        n /= 1024

def post_stream(url, data, out_path, chunk=4<<20, progress_every=0.5):
    t0 = time.time(); n = 0; last_t = t0; last_n = 0
    with requests.post(url, data={"data": data}, stream=True) as r:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            body = ""
            try: body = r.text[:2000]
            except: pass
            raise RuntimeError(f"Overpass error at {url}: {e}\n--- server said ---\n{body}") from None
        r.raw.decode_content = True
        with open(out_path, "wb") as f:
            for b in r.iter_content(chunk_size=chunk):
                if not b: continue
                f.write(b); n += len(b)
                now = time.time()
                if now - last_t >= progress_every:
                    dt = now - t0
                    inst = (n - last_n) / (now - last_t) if now > last_t else 0
                    avg = n / dt if dt > 0 else 0
                    print(f"⬇️  {human(n)} in {dt:.1f}s | inst {human(inst)}/s, avg {human(avg)}/s")
                    last_t = now; last_n = n
    print(f"✅ Downloaded {n:,} bytes in {time.time()-t0:.2f}s → {out_path}")
    # If it's suspiciously tiny, print it to help debugging
    if n < 2048:
        try:
            print("--- tiny response body ---")
            print(Path(out_path).read_text(errors="replace"))
        except Exception:
            pass

def fetch_with_fallback(query, out_path):
    last_err = None
    for url in MIRRORS:
        print(f"🌐 Trying {url} …")
        try:
            post_stream(url, query, out_path)
            return
        except Exception as e:
            last_err = e
            print(f"✗ Failed on {url}: {e}\n")
    raise last_err

def fetch_json_with_fallback(query: str) -> dict:
    last_err = None
    for url in MIRRORS:
        try:
            r = requests.post(url, data={"data": query}, timeout=240)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            continue
    if last_err:
        raise last_err
    raise RuntimeError("All mirrors failed")

def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ids_path = OUT / f"overpass_ids_london_{ts}.json"
    raw_path = OUT / f"overpass_raw_london_{ts}.json"

    print("⏳ Stage A: fetch Tube relation IDs (bbox + exact network)…")
    fetch_with_fallback(Q_IDS, ids_path)

    # Parse relation ids
    data = json.loads(ids_path.read_text(errors="replace"))
    rels = [el["id"] for el in data.get("elements", []) if el.get("type") == "relation"]
    if not rels:
        raise RuntimeError("No route relations returned. Check response above and consider widening query.")
    print(f"🆔 Found {len(rels)} Tube relation IDs")

    # Stage B: fetch bodies + members for these relations
    print("⏳ Stage B: fetch relation bodies and members…")
    query = q_members(rels)
    print(query)
    fetch_with_fallback(query, raw_path)
    #fetch_with_fallback(q_members(rels), raw_path)

    # --- Stage C: fetch Tube stations and merge into raw ---
    print("⏳ Stage C: fetch Tube stations (bbox) and merge …")
    st = fetch_json_with_fallback(STATIONS_Q)
    
    # Load the Stage‑B raw file, merge station nodes, write a merged file
    raw_doc = json.loads(raw_path.read_text(errors="replace"))
    n_before = len(raw_doc.get("elements", []))
    s_added = len(st.get("elements", []))
    raw_doc.setdefault("elements", []).extend(st.get("elements", []))
    
    merged_path = OUT / f"{raw_path.stem}_with_stations.json"
    merged_path.write_text(json.dumps(raw_doc, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Merged {s_added} stations into raw (elements {n_before} → {len(raw_doc['elements'])}) → {merged_path}")
    print("👉 Use the *merged* file with your processor so stations appear.")

if __name__ == "__main__":
    main()
