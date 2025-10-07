# save as process_tokyo_overpass.py
import argparse, gzip, json, time
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional

import geopandas as gpd
from shapely.geometry import Point, LineString

def load_overpass_json(path: Path) -> Dict[str, Any]:
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8", errors="replace"))

def write_geojson_safe(gdf: gpd.GeoDataFrame, path: Path):
    if gdf.empty:
        path.write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")
    else:
        gdf.to_file(path, driver="GeoJSON")

def build_node_index(elements: List[dict]) -> Dict[int, Tuple[float, float]]:
    idx: Dict[int, Tuple[float, float]] = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            nid = el.get("id")
            if isinstance(nid, int):
                idx[nid] = (float(el["lon"]), float(el["lat"]))
    return idx

def collect_relation_member_way_ids(elements: List[dict]) -> Set[int]:
    way_ids: Set[int] = set()
    rels = 0
    for el in elements:
        if el.get("type") != "relation":
            continue
        tags = el.get("tags") or {}
        if tags.get("route") not in ("subway", "light_rail"):
            continue
        rels += 1
        for m in el.get("members", []):
            if m.get("type") == "way" and isinstance(m.get("ref"), int):
                way_ids.add(m["ref"])
    print(f"🔗 route relations: {rels:,} | member way ids: {len(way_ids):,}")
    return way_ids

def way_coords(way: dict, node_ix: Dict[int, Tuple[float, float]]) -> Optional[List[Tuple[float, float]]]:
    geom = way.get("geometry")
    if isinstance(geom, list) and len(geom) >= 2 and "lon" in geom[0]:
        return [(float(pt["lon"]), float(pt["lat"])) for pt in geom if "lon" in pt and "lat" in pt]
    node_ids = way.get("nodes")
    if isinstance(node_ids, list) and len(node_ids) >= 2:
        coords = [node_ix.get(nid) for nid in node_ids]
        coords = [c for c in coords if c is not None]
        if len(coords) >= 2:
            return coords
    return None

def tag_line_is_route(tags: dict, include_tram: bool) -> bool:
    rwy = tags.get("railway")
    route = tags.get("route")
    if rwy in ("subway", "light_rail", "rapid_transit"):
        return True
    if rwy == "rail" and (tags.get("subway") == "yes" or tags.get("tunnel") in ("yes", "true")):
        return True
    if route in ("subway", "light_rail"):
        return True
    if include_tram and rwy == "tram" and (tags.get("subway") == "yes" or route in ("subway", "light_rail")):
        return True
    return False

def node_is_station(tags: dict) -> bool:
    st = tags.get("station")
    return (st == "subway") or (tags.get("railway") == "station" and (st == "subway" or tags.get("subway") == "yes"))

def main():
    ap = argparse.ArgumentParser(description="Process saved Overpass JSON (Tokyo subway/light_rail) into GeoJSON layers.")
    ap.add_argument("input", type=Path, help="Path to saved Overpass JSON (.json or .json.gz)")
    ap.add_argument("--out", type=Path, default=Path("data_tokyo"), help="Output directory (default: data_tokyo)")
    ap.add_argument("--prefix", type=str, default="tokyo_subway", help="Output filename prefix (default: tokyo_subway)")
    ap.add_argument("--union-tags", action="store_true", help="Union relation members with tag-matched lines")
    ap.add_argument("--include-tram", action="store_true", help="Allow tram lines when tagged like subway/light_rail")
    args = ap.parse_args()

    out = args.out; out.mkdir(parents=True, exist_ok=True)
    routes_path   = out / f"{args.prefix}_routes.geojson"
    stations_path = out / f"{args.prefix}_stations.geojson"
    all_path      = out / f"{args.prefix}_all.geojson"

    print(f"📥 Loading {args.input} …")
    t0 = time.time(); data = load_overpass_json(args.input); print(f"✅ Loaded in {time.time()-t0:.2f}s")

    els = data.get("elements", [])
    ways  = [e for e in els if e.get("type") == "way"]
    nodes = [e for e in els if e.get("type") == "node"]
    print(f"🧮 elements — ways: {len(ways):,}, nodes: {len(nodes):,}")

    node_ix = build_node_index(els)
    member_ids = collect_relation_member_way_ids(els)

    # Build route lines (relation members)
    line_rows, line_geoms = [], []
    found_members = 0

    for w in ways:
        wid = w.get("id")
        if isinstance(wid, int) and wid in member_ids:
            coords = way_coords(w, node_ix)
            if coords and len(coords) >= 2:
                line_geoms.append(LineString(coords))
                tags = w.get("tags") or {}
                line_rows.append({
                    "id": wid,
                    "railway": tags.get("railway"),
                    "subway": tags.get("subway"),
                    "route": tags.get("route"),
                    "tunnel": tags.get("tunnel"),
                    "name": tags.get("name"),
                    "in_route": True,
                })
                found_members += 1

    # Optional: union tag-matched lines not in relations
    extra = 0
    if args.union_tags:
        member_ids_set = member_ids  # already a set
        for w in ways:
            wid = w.get("id")
            if not isinstance(wid, int) or wid in member_ids_set:
                continue
            tags = w.get("tags") or {}
            if tag_line_is_route(tags, include_tram=args.include_tram):
                coords = way_coords(w, node_ix)
                if coords and len(coords) >= 2:
                    line_geoms.append(LineString(coords))
                    line_rows.append({
                        "id": wid,
                        "railway": tags.get("railway"),
                        "subway": tags.get("subway"),
                        "route": tags.get("route"),
                        "tunnel": tags.get("tunnel"),
                        "name": tags.get("name"),
                        "in_route": False,
                    })
                    extra += 1
        if extra:
            print(f"➕ added {extra:,} tag-matched lines (union-tags)")

    routes_gdf = gpd.GeoDataFrame(line_rows, geometry=line_geoms, crs="EPSG:4326")

    # Build station points
    st_rows, st_geoms = [], []
    for n in nodes:
        tags = n.get("tags") or {}
        if node_is_station(tags):
            st_geoms.append(Point(float(n["lon"]), float(n["lat"])))
            st_rows.append({
                "id": n.get("id"),
                "name": tags.get("name"),
                "railway": tags.get("railway"),
                "station": tags.get("station"),
                "subway": tags.get("subway"),
            })
    stations_gdf = gpd.GeoDataFrame(st_rows, geometry=st_geoms, crs="EPSG:4326")

    print(f"✅ routes kept: {len(routes_gdf):,} (members found with coords: {found_members:,}) | stations: {len(stations_gdf):,}")

    # Writes (same filenames)
    print(f"💿 Writing {routes_path.name} + {stations_path.name} + {all_path.name}")
    write_geojson_safe(routes_gdf, routes_path)
    write_geojson_safe(stations_gdf, stations_path)
    # union for *_all
    all_gdf = gpd.GeoDataFrame(pd.concat([routes_gdf, stations_gdf], ignore_index=True), geometry="geometry", crs="EPSG:4326") if len(routes_gdf) or len(stations_gdf) else gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    write_geojson_safe(all_gdf, all_path)

if __name__ == "__main__":
    import pandas as pd  # used only for concat
    main()
