import geopandas as gpd

# Define target states
selected_states = ['New Hampshire', 'Vermont', 'Massachusetts']

# Load full U.S. states GeoJSON (or shapefile)
states = gpd.read_file('../data/gz_2010_us_040_00_20m.json')

# Filter states by NAME
states_filtered = states[states['NAME'].isin(selected_states)]

# Save filtered states as its own GeoJSON layer
states_filtered.to_file('states_layer.geojson', driver='GeoJSON')
print(f"Saved {len(states_filtered)} states to 'states_layer.geojson'")

# Loaded County data from Tiger: 
# https://catalog.data.gov/dataset/tiger-line-shapefile-2021-nation-u-s-counties-and-equivalent-entities

# Load counties shapefile — just give it the .shp file (GeoPandas reads the rest)
# This is a "Shapefile" which is really a set of files.  They are assumed
# to be in this directory.
# Note: More recent?  Any data problem with state data?  precision?
counties = gpd.read_file('tl_2021_us_county.shp')

print(counties.columns)

# Filter counties by STATEFP (FIPS codes)
target_fips = states_filtered['STATE'].unique()
counties_filtered = counties[counties['STATEFP'].isin(target_fips)]

# Save filtered counties GeoJSON layer
counties_filtered.to_file('counties_layer.geojson', driver='GeoJSON')
print(f"Saved {len(counties_filtered)} counties to 'counties_layer.geojson'")
