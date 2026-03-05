import sys
import os
import json
import osmnx as ox

sys.path.append("c:/Users/sahoo/OneDrive/Desktop/LLM_RAG")
from openrouter_client import generate_osm_tags

query = "Find suitable locations in Solapur District near major roads to make new schools"
print("Generating tags...")
tags = generate_osm_tags(query)
print("Tags:", tags)

print("Fetching geometry for Solapur District...")
try:
    boundary = ox.geocode_to_gdf("Solapur District")
    boundary = boundary.to_crs(epsg=4326)
    roi_geom = boundary.geometry.iloc[0]
    print("Geometry fetched.")
except Exception as e:
    print("Geocode failed:", e)
    sys.exit(1)

print("Fetching features with tags...")
try:
    features = ox.features_from_polygon(roi_geom, tags=tags)
    print(f"Found {len(features)} features.")
except Exception as e:
    print("Feature fetch failed:", e)

