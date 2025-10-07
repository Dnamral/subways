import geopandas as gpd
import os
from shapely import wkt

# --- Input paths: Île-de-France Mobilités GeoJSON ---
stations_path = "./data/schema_gares-gf.geojson"
routes_path = "./data/schema_trace_fermetrotram-gf.geojson"

# --- Load datasets ---
stations = gpd.read_file(stations_path)
routes = gpd.read_file(routes_path)

print("Original CRS (stations):", stations.crs)
print("Original CRS (routes):", routes.crs)

print("Raw Lambert-93 geometry sample:", routes.geometry.iloc[0])
print("Bounds before reprojection:", routes.total_bounds)

# --- Step 1: Force known correct CRS ---
print("Overriding CRS: forcing EPSG:2154 (Lambert-93)...")
stations.set_crs(epsg=2154, allow_override=True, inplace=True)
routes.set_crs(epsg=2154, allow_override=True, inplace=True)

print("CRS after override:")
print("  stations:", stations.crs)
print("  routes  :", routes.crs)

# --- Step 2: Reproject to WGS84 (EPSG:4326) for D3/Leaflet ---
stations = stations.to_crs(epsg=4326)
routes = routes.to_crs(epsg=4326)

# --- Step 3: Drop Z-dimension if present ---
def drop_z(geom):
    try:
        return geom.to_2d()
    except AttributeError:
        # fallback for older Shapely
        from shapely import wkt
        from shapely.wkt import dumps, loads
        return loads(dumps(geom, output_dimension=2))

stations["geometry"] = stations["geometry"].apply(drop_z)
routes["geometry"] = routes["geometry"].apply(drop_z)

# --- Step 4: Set CRS explicitly before export ---
stations.crs = "EPSG:4326"
routes.crs = "EPSG:4326"

print("Bounds after reprojection:")
print("  stations:", stations.total_bounds)
print("  routes  :", routes.total_bounds)

# --- Step 5: Export to cleaned GeoJSON ---
os.makedirs("output", exist_ok=True)
stations.to_file("output/paris_stations.geojson", driver="GeoJSON")
routes.to_file("output/paris_routes.geojson", driver="GeoJSON")

print("✅ Exported cleaned GeoJSON files to ./output/")
