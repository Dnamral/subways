import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Load CSV
df = pd.read_csv("stations.csv", sep=';')

# Build GeoDataFrame using x and y as Lambert-93 (EPSG:2154)
geometry = [Point(xy) for xy in zip(df['x'], df['y'])]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:2154")

# Reproject to WGS84
gdf = gdf.to_crs("EPSG:4326")

# Save valid GeoJSON
gdf.to_file("output/stations_from_csv.geojson", driver="GeoJSON")

print("✅ Saved corrected GeoJSON to output/stations_from_csv.geojson")
