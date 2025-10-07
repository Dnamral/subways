import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString

# 1. Load GTFS stops (station locations)
stops_df = pd.read_csv("../data/stops.txt")

# Filter: only actual stations (not entrances/platforms)
# GTFS location_type = 1 for parent station
if 'location_type' in stops_df.columns:
    stops_df = stops_df[stops_df['location_type'] == 1]

# Create GeoDataFrame of station points
stops_gdf = gpd.GeoDataFrame(
    stops_df,
    geometry=gpd.points_from_xy(stops_df.stop_lon, stops_df.stop_lat),
    crs="EPSG:4326"  # GTFS uses WGS84
)

# 2. Load GTFS shapes (route paths)
shapes_df = pd.read_csv("../data/shapes.txt")

# Group by shape_id and order by shape_pt_sequence to create LineStrings
lines = []
for shape_id, group in shapes_df.groupby("shape_id"):
    group = group.sort_values("shape_pt_sequence")
    coords = list(zip(group.shape_pt_lon, group.shape_pt_lat))
    line = LineString(coords)
    lines.append({"shape_id": shape_id, "geometry": line})

# Create GeoDataFrame of route paths
shapes_gdf = gpd.GeoDataFrame(lines, crs="EPSG:4326")

# 3. Export both to GeoJSON
stops_gdf.to_file("nyc_subway_stations.geojson", driver="GeoJSON")
shapes_gdf.to_file("nyc_subway_routes.geojson", driver="GeoJSON")
