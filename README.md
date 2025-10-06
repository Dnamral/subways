# Subways 

This project uses [D3.js](https://d3js.org) to render a medium-detail 
Mercator projection map of subway stops and routes of a few select
cities using GeoJSON data. 

The rendering in __D3__ is currently fairly primitive.  __D3__ is loaded
dynamically in the entry point file `index.html`.  Basic `css` styling
is done inline and a simple `script` is called (not a `module`).  The
skeleton of the `index.html` looks like the following:

```
..
<head>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
   .. 
  </style>
</head>
<body>
  <div id="tooltip" class="tooltip" style="display:none;"></div>
  <script src="nyc_paris_main.js"></script>
</body>
```

The primary (and currently only) `javascript` file performs a
number of rendering tasks described below.

The directory structure tells the story:

<pre>
project-root/
├── data/
│   ├── raw/
│   └── processed/
├── filter/
│   ├── raw/
│   └── processed/
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
├── README.md
├── index.html
├── nyc_paris_subway.js
├── convert_paris_transit.py ❌
└── convert_paris_gares.py 
</pre>

  This is simply
nyc_paris_main.js which is called from index.js and served by the simple
python server

`python3 -m http.server 8000`

https://prim.iledefrance-mobilites.fr/en/jeux-de-donnees/emplacement-des-gares-idf-data-generalisee
rendering and data transformation.  Look in
the following places for the beginning of the trail to both pieces.

- A __D3__ rendering script to render a medium-detail Mercator map
of selected Northeast US states using GeoJSON in `index.html`
- Map data held in `data/northeast_us.geojson`


## Actual Steps Taken:

Now that can hit reality in multiple ways.

We show some of the challenges even at the basic level.  That is,
getting map data at the correct resolution and the _unsolved problem_
of synchronizing __polygon shapes__ between __geojson__ map data
of differing resolutions.

As a plainly put example, when you have a source for state data that consists
of state polygons of ~250 points and you join that to another data source
with county polygons of ~250 points you can figure out that the county 
data will be at a *higher resolution* and that coloring the county 
(using a chloropleth approach for example) will lead to seeing counties
at the border of states zigzagging over state lines.  So you immediately
have non-trivial problems in the *basic* display of map data.

Then there are the problems of:
- Getting the data by download
- reducing it (Going from 50 states to far fewer will lead to much smaller files)
- ultimately cutting down the resolution (something we really have not done)
- stitching county map data to publicly available data per county

## Getting the Data

# For States Map (States Polygons with Codes):

gz_2010_us_040_00_20m.json

TODO: where did we get this from?

You can *cheat* and get this from a __github__ source:
https://github.com/kjhealy/us-county/blob/master/data/geojson/gz_2010_us_040_00_20m.json

Or you can find the needle in the haystack (it's here as of 2024):

https://www2.census.gov/geo/tiger/GENZ2010/gz_2010_us_040_00_20m.zip

In `zip` format it is approximately 634K. 

So now you can unzip to the following files:

```
-15558 Dec  9  2011 gz_2010_us_040_00_20m.xml
-10126 Sep 13  2011 gz_2010_us_040_00_20m.dbf
-165 Sep 13  2011 gz_2010_us_040_00_20m.prj
-830916 Sep 13  2011 gz_2010_us_040_00_20m.shp
-516 Sep 13  2011 gz_2010_us_040_00_20m.shx
```

Then use __geopandas__ (python based) by installing using your tool of choice.
The following is for using micromamba (much preferred over conda for speed
purposes).  Either setup a new environment or in an environment you trust:

```
micromamba install geopandas -c conda-forge
```
# The Following is Really Not For This Project

But we keep it here in case we ever want to include other
geographic data.  This is also in our project containing 
maps of some of the states in the US Northeast.  That directory
should contain a decent README.md that discusses some of the
technical issues around polygons and granularity.

# For County Map (County Polygons with Codes):

There is a note that the following source was used for county data.
https://catalog.data.gov/dataset/tiger-line-shapefile-2021-nation-u-s-counties-and-equivalent-entities 

So this is a little more than it seems.  You are downloading a __shapefile__ which
is actually a collection of files including an __.shp file__.  See below for
__geopandas__ usage to _read_ these files.

# Filtering the Data in Maps

##  Use Geopandas for filtering data in maps

Ultimately, we used __geopandas__.  So if you are using a micromamba environment, first
install __geopandas__.

```
micromamba install geopandas
```

# Write a python script to reduce the data.

See the [Filter File for Large US Dataset File](filter/filter_geo.py)
for filtering down the large dataset in 

```
gz_2010_us_040_00_20m.json 
```

to 

```
states_layer.geojson
```

Note that the __county data__ is also filtered in the 
[Counties Filter File](filter/filter_geo.py)

This filtration is done in the same file because we actually use the filtered
states object (returned from geopandas.read_file) to further filter the
counties.  These are then put in the file [Counties
Layer](data/counties_layer.geojson)


# County Data for Choropleth

For county data we used a file (does not currently exist by this name which
is given solely so that it might be located from original source).

```
PLACES__Local_Data_for_Better_Health__County_Data_2024_release_20250508.csv
```

This was changed to a shorter name:

```
filter/PLACES_County_Data_2024.csv
```

TODO: How did we stitch the county data to the data (per county) driving the
chloropleth? See 

```
./filter/filter_places.py
```

Note that this file simply uses __pandas__ and __DataFrames__ to select columns
(particularly obesity by county data) to the file:

```
data/obesity_by_county_csv
```

Once you add the data file, open index.html in your browser.

# Project Tokyo

We are now trying to get a little bit more _homogeneous_ in our approach to data
and have decided to try out __OSM__ (Open Street Map) through the __Overpass__ API.

I have chosen a pre-existing `micromamba` environment of `cs109bmamba.`  You
can check your environment by performing

```
micromamba env list
```

You can check by running this:

```
micromamba list | grep geopandas
```

On my system this returned

```
  geopandas                      1.0.1            pyhd8ed1ab_3                 conda-forge
  geopandas-base                 1.0.1            pyha770c72_3                 conda-forge
```

Then we need `requests` and `osmtogeojson`.  `osmtogeojson` is not available on
`conda-forge`, so we simply use __pip__ to install it.  Note that if you are in
a `micromamba` active environment installing with `pip` will install into the
`miniconda` environment.  At least at a basic working level you _should_ be
able to reference that package.

```
micromamba install -c conda-forge requests
pip install osmtogeojson
```

This is unfortunately creating the project after the fact.  Let's try for NYC.
We have the routes and stops data.  Unfortunately, they don't seem to have
intersection.

From __comments__ in the file ./filter/filter_nyc_subways.py we seem to have
originally picked up GTFS (General Transit Feed Specification).  Possibly by
going to the MTA site.  This is located at https://www.mta.info/developers.
When clicking on __static GTFS Data I chose __Regular GTFS__ and the immediate
download showed that it had already been downloaded as __gtfs_subway.zip__.

There is indeed a `gtfs_subway.zip` in ./data/.

```
unzip -l gtfs_subway.zip
```

Shows the following data which has been unzipped into ./data/

```
Archive:  gtfs_subway.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
      162  06-23-2025 09:05   agency.txt
       71  06-23-2025 09:03   calendar_dates.txt
      208  06-23-2025 09:05   calendar.txt
    11397  06-03-2025 18:29   routes.txt
  5801588  06-23-2025 09:05   shapes.txt
 36071419  06-23-2025 09:05   stop_times.txt
    63812  06-23-2025 09:05   stops.txt
     8558  06-23-2025 09:05   transfers.txt
  1543258  06-23-2025 09:05   trips.txt
---------                     -------
```

So if we were to reconstruct we might be able to write a `curl` if MTA supports this.

The file that then does data cleaning and translation on the files above is

```
./filter/filter_nyc_subways.py
```

which operates on 

```
./data/stops.txt
```

by the following mechanisms in __python__ in the 
[Data Extraction and Filtration File for NYC Subway Data](filter/filter_nyc_subways.py)

```python
import pandas as pd
import geopandas as gpd
import shapely.geometry import Point, LineString

# ... create a DataFrame from csv data file and check on
# existence of column location_type.  Filter out all columns
# except those whose value is 1

stops_gdf = gpd.GeoDataFrame(
  stops_df,
  geometry=gpd.points_from_xy(stops_df.stop_lon, stops_df.stop_lat),
  crs="EPSG:4326"  # GTFS uses WGS84
)
```

Although appropriate for more granular documentation, `geometry`
constructed by the __geopandas__ API `points_from_xy` is
a `GeoSeries` of `shapely.geometry.Point` objects.  This is
equivalent to:

```
gpd.GeoSeries([Point(x, y) for x, y in zip(df.longitude, df.latitude)])
```

Python-wise, this is a __list comprehension__ with __unpacking__.
The __list comprehension__ is ubiquitous in __python__. 
__zip__ creates an __iterator__ of __tuples__.
`x,y in ... ` __unpacks__ each 2-tuple from __zip__ into x and y.
This returns a __list__ of __Points__ objects.

It would be natural to wonder why __geopandas__ would return a
__shapely__ object.  That is because __geopandas__ is built on
top of __shapely__.  The __shapely__ package provides 
geometric objects like Point, LineString, Polygon, etc. and
__geopandas___ provides Pandas-like structures (GeoSeries, 
GeoDataFrame) that wrap and manage __shapely__ geometries with 
CRS-aware behavior.  

## Shapely and GeoPandas Version Mismatch Possibility is Real

Although probably only if dealing with old versions.  The dependency
tree is something like the following:

```
GeoPandas
 ├── depends on Pandas
 ├── depends on Pyproj (for CRS handling)
 ├── depends on Fiona (for file I/O)
 ├── depends on Shapely (for geometry ops)
 └── depends on GDAL (indirectly through Fiona)

Shapely
 └── uses GEOS (C++ spatial library)
 ```

 So basically you can check this with

 ```
 conda list | grep -E 'geopandas|shapely'
 ```

And beware it you are not using __shapely__ above 2.0
with __geopandas__ above 0.14.

In terms of actual specifications of how to interpret the data `crs`
(Coordinate Reference System) are __standards__ __geopandas__ uses
to interpret the coordinate system, units(degrees, meters,...),
the projection(spherical Earth, flat map) and 

> how to interpret (x,y) numerically and geographically.

This last statement is a little amorphous but these subjects
can be somewhat steep (or deep) depending on your perspective.

Informally, however, I once looked into the effect of __curvature__
over an area the size of the subway in Manhattan and I believe
(which you should not unless you check) that over the curved Earth
distance of 10km the greatest distance of any point from a flat
Earth (Euclidean model) is less than one millimeter.

You will have to know the actual CRS used by your data source.
The match is important.  What it actually is is good to know, but
not essential over small distances.

```
EPSG:4326   WGS84 — lat/lon in degrees          Default for GPS. Used by Google Maps, OpenStreetMap, etc.
EPSG:3857   Web Mercator projection             Used for slippy maps. Units in meters, but distortion increases near poles.
EPSG:2263   NAD83 / New York Long Island (ft)   Used by NYC-specific data in State Plane coordinates. Units are in feet.
EPSG:26918  NAD83 / UTM zone 18N                Good for mid-Atlantic US. Units in meters.
```

By memory, Paris is funky.  I do not believe that we currently use any NAD83 data.

## You can switch to different units in your data

This is not tested, but you can project to feet-based CRS 
for distance calculations by the following code:

```python
gdf = gdf.to_crs("EPSG:2263")
```

## This file then creates routes that are paths

```python
lines = []
for shape_id, group in shapes_df.groupby("shape_id"):
    group = group.sort_values("shape_pt_sequence")
    coords = list(zip(group.shape_pt_lon, group.shape_pt_lat))
    line = LineString(coords)
    lines.append({"shape_id": shape_id, "geometry": line})
```

This indicates a __shapely__ download install.  Suggested download path:

```
micromamba install -c conda-forge shapely
```

We have to look at two further files in the __filter__ directory:


Because we have to make explicit the connection between stops and routes.
This is not given to you directly.  You have to follow the following data path:

```
stops.txt       ← stop_id
   ↕
stop_times.txt  ← trip_id + stop_id
   ↕
trips.txt       ← trip_id + route_id + shape_id
   ↕
routes.txt      ← route_id  ← e.g. A, 6, Q
```

This might now have been done.  We might have been content to just print
points (stops) and render routes (paths) with no connection.

# github

Obviously, a README.md is not where to store this information.  But we are making
sure that all of our various fragments are stored in a github repository, and
this stores a temporary 'marker' of this activity:

```
echo "# subways" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:Dnamral/subways.git
git push -u origin main
```
# subways
