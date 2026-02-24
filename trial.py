import ee
import geemap
import os
import osmnx as ox
import geopandas as gpd
import rasterio
from rasterio import features
import numpy as np
from scipy.ndimage import distance_transform_edt

# --------------------------------------------------
# 1️⃣ INITIALIZE
# --------------------------------------------------

ee.Initialize(project='llm-gis-project')
os.makedirs("data", exist_ok=True)

place_name = "Navi Mumbai, Maharashtra, India"

# --------------------------------------------------
# 2️⃣ FETCH BOUNDARY
# --------------------------------------------------

boundary = ox.geocode_to_gdf(place_name)
boundary = boundary.to_crs(epsg=4326)
roi_geom = boundary.geometry.iloc[0]
bounds = roi_geom.bounds
roi = ee.Geometry.Rectangle(bounds)

# --------------------------------------------------
# 3️⃣ FETCH DEM + COMPUTE SLOPE IN GEE
# --------------------------------------------------

dem = ee.Image("USGS/SRTMGL1_003").clip(roi)
slope = ee.Terrain.slope(dem)

slope_path = "data/slope.tif"

geemap.ee_export_image(
    slope,
    filename=slope_path,
    scale=30,
    region=roi
)

print("Slope downloaded from GEE")

# --------------------------------------------------
# 4️⃣ FETCH ROADS FROM OSM
# --------------------------------------------------

G = ox.graph_from_place(place_name, network_type='drive')
roads = ox.graph_to_gdfs(G, nodes=False)
roads = roads.to_crs(boundary.crs)

# --------------------------------------------------
# 5️⃣ RASTERIZE ROADS
# --------------------------------------------------

with rasterio.open(slope_path) as src:
    transform = src.transform
    shape = src.shape

road_raster = features.rasterize(
    [(geom, 1) for geom in roads.geometry],
    out_shape=shape,
    transform=transform,
    fill=0,
    dtype='uint8'
)

# --------------------------------------------------
# 6️⃣ DISTANCE TO ROADS
# --------------------------------------------------

road_distance = distance_transform_edt(1 - road_raster)
road_score = 1 - (road_distance / road_distance.max())

# --------------------------------------------------
# 7️⃣ NORMALIZE SLOPE (flatter = better)
# --------------------------------------------------

with rasterio.open(slope_path) as src:
    slope_data = src.read(1)

# Avoid division by zero
if slope_data.max() != 0:
    slope_score = 1 - (slope_data / slope_data.max())
else:
    slope_score = np.ones_like(slope_data)

# --------------------------------------------------
# 8️⃣ WEIGHTED OVERLAY
# --------------------------------------------------

final_score = (0.6 * road_score) + (0.4 * slope_score)

# --------------------------------------------------
# 9️⃣ EXTRACT TOP 10 LOCATIONS
# --------------------------------------------------

flat = final_score.flatten()
top_indices = np.argpartition(flat, -10)[-10:]
rows, cols = np.unravel_index(top_indices, final_score.shape)

locations = []

with rasterio.open(slope_path) as src:
    for r, c in zip(rows, cols):
        lon, lat = src.transform * (c, r)
        score = final_score[r, c]
        locations.append({
            "latitude": float(lat),
            "longitude": float(lon),
            "score": float(score)
        })

print("\nRecommended EV Locations:\n")
for loc in locations:
    print(loc)