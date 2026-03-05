import requests
import json
import os

BASE_URL = "http://127.0.0.1:8000"

def test_area_limit():
    print("Testing Area Limit with 'Solapur District'...")
    payload = {
        "query": "new schools",
        "place_name": "Solapur District"
    }
    try:
        response = requests.post(f"{BASE_URL}/run-analysis", json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        if response.status_code == 400 and "Search area too large" in data.get("error", ""):
            print("SUCCESS: Area limit correctly triggered.")
        else:
            print("FAILURE: Area limit NOT triggered or unexpected response.")
    except Exception as e:
        print(f"ERROR: {e}")

def test_tag_generation():
    print("\nTesting OSM Tag Generation logic...")
    payload = {
        "query": "Find suitable locations in Karmala, Solapur for a new school near major roads",
        "place_name": "Karmala, Solapur"
    }
    try:
        # We'll just check if features are returned or if the tags (visible in logs) are better
        response = requests.post(f"{BASE_URL}/run-analysis", json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        # If it returns 200, it means it found SOMETHING or at least didn't crash.
        # The key is checking the backend logs for what tags were generated.
        if response.status_code == 200:
            print("SUCCESS: Small area query processed.")
        else:
            print(f"FAILURE: Status {response.status_code}, {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_area_limit()
    test_tag_generation()
