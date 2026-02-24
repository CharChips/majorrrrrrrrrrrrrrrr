import json
import os
import numpy as np
import rasterio
from rasterio import features
from scipy.ndimage import distance_transform_edt
import osmnx as ox
import ee
import geemap

place_name = "Navi Mumbai, Maharashtra, India"

ee.Initialize(project='llm-gis-project')


def execute_workflow(workflow_path="generated_workflow.json"):

    with open(workflow_path, "r") as f:
        workflow = json.load(f)

    data_store = {}

    # -----------------------------------------
    # Fetch Boundary + Base DEM once
    # -----------------------------------------

    boundary = ox.geocode_to_gdf(place_name)
    boundary = boundary.to_crs(epsg=4326)
    roi_geom = boundary.geometry.iloc[0]
    bounds = roi_geom.bounds
    roi = ee.Geometry.Rectangle(bounds)

    dem = ee.Image("USGS/SRTMGL1_003").clip(roi)

    os.makedirs("data", exist_ok=True)
    os.makedirs("static", exist_ok=True)

    dem_path = "data/dem.tif"

    geemap.ee_export_image(
        dem,
        filename=dem_path,
        scale=30,
        region=roi
    )

    with rasterio.open(dem_path) as src:
        base_raster = src.read(1)
        transform = src.transform
        raster_bounds = src.bounds

    data_store["base_raster"] = base_raster
    data_store["transform"] = transform
    data_store["bounds"] = raster_bounds

    # -----------------------------------------
    # Execute Workflow Steps
    # -----------------------------------------

    for step in workflow["steps"]:

        tool = step["tool"]
        inputs = step.get("inputs", {})
        params = step.get("parameters", {})
        outputs = step.get("outputs", {})

        # -------------------------------
        # gdalwarp (mocked)
        # -------------------------------
        if tool == "gdalwarp":
            input_name = inputs["input_raster"]
            data_store[outputs["output_raster"]] = data_store[input_name]

        # -------------------------------
        # DistanceRaster
        # -------------------------------
        elif tool == "DistanceRaster":

            G = ox.graph_from_place(place_name, network_type='drive')
            roads = ox.graph_to_gdfs(G, nodes=False)

            road_raster = features.rasterize(
                [(geom, 1) for geom in roads.geometry],
                out_shape=data_store["base_raster"].shape,
                transform=data_store["transform"],
                fill=0,
                dtype='uint8'
            )

            road_distance = distance_transform_edt(1 - road_raster)

            data_store[outputs["distance_raster"]] = road_distance

        # -------------------------------
        # NormalizeRaster
        # -------------------------------
        elif tool == "NormalizeRaster":

            input_name = inputs["input_raster"]
            raster = data_store[input_name]

            max_val = np.max(raster)
            normalized = raster / max_val if max_val != 0 else raster

            data_store[list(outputs.values())[0]] = normalized

        # -------------------------------
        # WeightedOverlay
        # -------------------------------
        elif tool == "WeightedOverlay":

            input1 = data_store[inputs["input_raster"]]
            input2 = data_store[inputs["weight_raster"]]

            combined = (0.6 * input1) + (0.4 * input2)

            data_store[list(outputs.values())[0]] = combined

        # -------------------------------
        # ExtractTopLocations
        # -------------------------------
        elif tool == "ExtractTopLocations":

            raster = data_store[inputs["input_raster"]]
            flat = raster.flatten()
            top_n = params.get("num_locations", 10)

            indices = np.argsort(flat)[-top_n:]
            rows, cols = np.unravel_index(indices, raster.shape)

            locations = []
            transform = data_store["transform"]

            for r, c in zip(rows, cols):
                lon, lat = transform * (c, r)
                score = raster[r, c]
                locations.append({
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "score": float(score)
                })

            data_store["final_locations"] = locations

    return data_store["final_locations"], data_store["bounds"]