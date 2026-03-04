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

# --------------------------------------------------
# CORE EV ENGINE FUNCTION
# --------------------------------------------------

def run_ev_analysis(place_name: str, geojson: dict = None):

    if geojson and 'features' in geojson and len(geojson['features']) > 0:
        import geopandas as gpd
        from shapely.geometry import shape
        geom = shape(geojson['features'][0]['geometry'])
        
        # Buffer points or lines into a valid AOI rectangle (approx 5km radius)
        if geom.geom_type in ['Point', 'LineString']:
            geom = geom.buffer(0.05).envelope
            
        boundary = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")
    else:
        try:
            boundary = ox.geocode_to_gdf(place_name)
            boundary = boundary.to_crs(epsg=4326)
        except TypeError:
            import geopandas as gpd
            from shapely.geometry import Point
            lat, lng = ox.geocode(place_name)
            # Create a ~5km box around the point
            geom = Point(lng, lat).buffer(0.05).envelope
            boundary = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")
        
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
    G = ox.graph_from_polygon(roi_geom, network_type='drive')
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

from pydantic import BaseModel
import json
from rag_pipeline import run_pipeline

class WorkflowRequest(BaseModel):
    query: str
    location: str = ""

class AnalysisRequest(BaseModel):
    place_name: str
    geojson: dict = None

@app.post("/generate-workflow")
def generate_workflow(request: WorkflowRequest):
    workflow = run_pipeline(request.query, request.location)
    with open("generated_workflow.json", "w") as f:
        json.dump(workflow, f, indent=4)
    return JSONResponse(content={"status": "success", "message": "Workflow generated.", "workflow": workflow})

@app.post("/run-analysis")
def analysis(request: AnalysisRequest):
    locations = run_ev_analysis(request.place_name, request.geojson)
    return JSONResponse(content=locations)

@app.get("/dem")
def get_dem():
    return FileResponse("data/slope.tif")

app.mount("/", StaticFiles(directory="static", html=True), name="static")