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
from openrouter_client import generate_workflow, generate_osm_tags, generate_feature_reasoning
from rag_pipeline import run_pipeline

class WorkflowRequest(BaseModel):
    query: str
    location: str = ""
    previous_workflow: dict = None
    feedback: str = None

class AnalysisRequest(BaseModel):
    query: str = ""
    place_name: str
    geojson: dict = None
    top_n: int = 10
    weights: dict = None

@app.post("/generate-workflow")
def generate_workflow_api(request: WorkflowRequest):
    workflow = run_pipeline(
        user_query=request.query, 
        location=request.location,
        previous_workflow=request.previous_workflow,
        feedback=request.feedback
    )
    with open("generated_workflow.json", "w") as f:
        json.dump(workflow, f, indent=4)
    return JSONResponse(content={"status": "success", "message": "Workflow generated.", "workflow": workflow})

@app.post("/run-analysis")
def analysis(request: AnalysisRequest):
    # Determine boundary
    if request.geojson and 'features' in request.geojson and len(request.geojson['features']) > 0:
        import geopandas as gpd
        from shapely.geometry import shape
        geom = shape(request.geojson['features'][0]['geometry'])
        if geom.geom_type in ['Point', 'LineString']:
            geom = geom.buffer(0.05).envelope
        boundary = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")
    else:
        try:
            boundary = ox.geocode_to_gdf(request.place_name)
            boundary = boundary.to_crs(epsg=4326)
        except TypeError:
            import geopandas as gpd
            from shapely.geometry import Point
            lat, lng = ox.geocode(request.place_name)
            geom = Point(lng, lat).buffer(0.05).envelope
            boundary = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")

    roi_geom = boundary.geometry.iloc[0]

    # 1. Ask LLM to generate OSM tags for the user's query
    osm_tags = generate_osm_tags(request.query) if request.query else {"amenity": True}

    # 2. Fetch all geometries matching these tags inside the boundary
    try:
        features = ox.features_from_polygon(roi_geom, tags=osm_tags)
        features = features.to_crs(epsg=4326)
    except Exception as e:
        print(f"No features found for tags: {osm_tags}")
        return JSONResponse(content={"type": "FeatureCollection", "features": []})

    # Drop null geometries and limit to top N results requested by UI
    top_n = request.top_n if request.top_n else 10
    features = features[~features.is_empty & features.is_valid].head(top_n)
    
    # 3. Ask LLM to generate a reason for each feature
    geojson_features = []
    
    # Pre-calculate centroids for the reasoning prompt
    for idx, row in features.iterrows():
        props = row.drop('geometry').dropna().to_dict()
        name = props.get('name', 'Unnamed Location')
        
        # Ask LLM for reasoning
        reason = generate_feature_reasoning(request.query, props)
        
        # Build strict valid GeoJSON Feature
        feature = {
            "type": "Feature",
            "geometry": row.geometry.__geo_interface__,
            "properties": {
                "name": name,
                "reason": reason,
                "raw_tags": props
            }
        }
        geojson_features.append(feature)

    feature_collection = {
        "type": "FeatureCollection",
        "features": geojson_features
    }

    return JSONResponse(content=feature_collection)

@app.post("/get-layers")
def get_layers(request: AnalysisRequest):
    import json
    # Determine boundary (clone from ev_analysis)
    if request.geojson and 'features' in request.geojson and len(request.geojson['features']) > 0:
        import geopandas as gpd
        from shapely.geometry import shape
        geom = shape(request.geojson['features'][0]['geometry'])
        if geom.geom_type in ['Point', 'LineString']:
            geom = geom.buffer(0.05).envelope
        boundary = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")
    else:
        try:
            boundary = ox.geocode_to_gdf(request.place_name)
            boundary = boundary.to_crs(epsg=4326)
        except TypeError:
            import geopandas as gpd
            from shapely.geometry import Point
            lat, lng = ox.geocode(request.place_name)
            geom = Point(lng, lat).buffer(0.05).envelope
            boundary = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")

    roi_geom = boundary.geometry.iloc[0]
    bounds = roi_geom.bounds
    roi = ee.Geometry.Rectangle(bounds)

    # 1. Population (WorldPop)
    pop = ee.ImageCollection("WorldPop/GP/100m/pop") \
            .filterBounds(roi) \
            .map(lambda img: img.clip(roi)) \
            .mean()
            
    pop_id = pop.getMapId({
        "min": 0, "max": 50, "palette": ['24126c', '1fff4f', 'd4ff50']
    })

    # 2. DEM / Elevation
    dem = ee.Image("USGS/SRTMGL1_003").clip(roi)
    dem_id = dem.getMapId({
        "min": 0, "max": 3000, "palette": ['006600', '002200', 'fff700', 'ab7634', 'c4d0ff', 'ffffff']
    })

    # 3. Vegetation (NDVI)
    ndvi = ee.ImageCollection("MODIS/061/MOD13Q1") \
             .filterBounds(roi) \
             .map(lambda img: img.clip(roi)) \
             .mean().select('NDVI')
    ndvi_id = ndvi.getMapId({
        "min": 0, "max": 8000, "palette": ['FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', '99B718', '74A901', '66A000', '529400', '3E8601', '207401', '056201', '004C00', '023B01', '012E01', '011D01', '011301']
    })

    # 4. Land Use (ESA WorldCover)
    land_use = ee.ImageCollection("ESA/WorldCover/v100").first().clip(roi)
    lu_id = land_use.getMapId({
        "bands": ['Map']
    })
    
    # 5. Roads (OSMnx)
    G = ox.graph_from_polygon(roi_geom, network_type='drive')
    roads = ox.graph_to_gdfs(G, nodes=False)
    roads_json = json.loads(roads.to_json())

    response = {
        "population": pop_id['tile_fetcher'].url_format,
        "dem": dem_id['tile_fetcher'].url_format,
        "vegetation": ndvi_id['tile_fetcher'].url_format,
        "land_use": lu_id['tile_fetcher'].url_format,
        "roads": roads_json
    }

    return JSONResponse(content=response)

@app.get("/dem")
def get_dem():
    return FileResponse("data/slope.tif")

app.mount("/", StaticFiles(directory="static", html=True), name="static")