import ee
import geemap
import os
import osmnx as ox
import rasterio
from rasterio import features
import numpy as np
from scipy.ndimage import distance_transform_edt
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# --------------------------------------------------
# INITIALIZE
# --------------------------------------------------

ee.Initialize(project='llm-gis-project')

app = FastAPI()

os.makedirs("data", exist_ok=True)
os.makedirs("static", exist_ok=True)

place_name = "Navi Mumbai, Maharashtra, India"

# --------------------------------------------------
# CORE EV ENGINE FUNCTION
# --------------------------------------------------

def run_ev_analysis():

    boundary = ox.geocode_to_gdf(place_name)
    boundary = boundary.to_crs(epsg=4326)
    roi_geom = boundary.geometry.iloc[0]
    bounds = roi_geom.bounds
    roi = ee.Geometry.Rectangle(bounds)

    # DEM + slope
    dem = ee.Image("USGS/SRTMGL1_003").clip(roi)
    slope = ee.Terrain.slope(dem)

    slope_path = "data/slope.tif"

    geemap.ee_export_image(
        slope,
        filename=slope_path,
        scale=30,
        region=roi
    )

    # Roads
    G = ox.graph_from_place(place_name, network_type='drive')
    roads = ox.graph_to_gdfs(G, nodes=False)

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

    road_distance = distance_transform_edt(1 - road_raster)
    road_score = 1 - (road_distance / road_distance.max())

    with rasterio.open(slope_path) as src:
        slope_data = src.read(1)

    slope_score = 1 - (slope_data / slope_data.max())

    final_score = (0.6 * road_score) + (0.4 * slope_score)

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

    return locations

# --------------------------------------------------
# API ROUTES
# --------------------------------------------------

@app.get("/run-analysis")
def analysis():
    locations = run_ev_analysis()
    return JSONResponse(content=locations)

@app.get("/dem")
def get_dem():
    return FileResponse("data/slope.tif")

app.mount("/", StaticFiles(directory="static", html=True), name="static")