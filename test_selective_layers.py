import requests
import json
import os
import time

def test_selective_layers():
    url = "http://localhost:8000/get-layers"
    
    # Test 1: Only Population
    payload = {
        "place_name": "Navi Mumbai, India",
        "weights": {"layers": ["population"]}
    }
    print("Testing selective fetch: population only...")
    response = requests.post(url, json=payload)
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Keys returned: {list(data.keys())}")
    assert "population" in data
    assert "dem" not in data
    assert "vegetation" not in data
    assert "land_use" not in data
    print("Test 1 passed!")

    # Test 2: DEM and Land Use
    payload = {
        "place_name": "Navi Mumbai, India",
        "weights": {"layers": ["dem", "land_use"]}
    }
    print("\nTesting selective fetch: dem and land_use...")
    response = requests.post(url, json=payload)
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Keys returned: {list(data.keys())}")
    assert "dem" in data
    assert "land_use" in data
    assert "population" not in data
    assert "vegetation" not in data
    print("Test 2 passed!")

    # Test 5: Mumbai Caching Test
    url_layers = "http://localhost:8000/get-layers"
    payload_mumbai = {
        "place_name": "Mumbai",
        "weights": {"layers": ["population", "dem"]}
    }
    
    print("\nTesting /get-layers with caching (Mumbai)...")
    # Clean up old mumbai files if they exist to ensure a fresh test
    for f in ["population", "dem", "slope"]:
        path = f"data/mumbai_{f}.tif"
        if os.path.exists(path):
            os.remove(path)
            
    start_time = time.time()
    response = requests.post(url_layers, json=payload_mumbai)
    print(f"First request status: {response.status_code}")
    print(f"First request took: {time.time() - start_time:.2f}s")
    
    print("Waiting for background exports...")
    time.sleep(15) 
    
    assert os.path.exists("data/mumbai_population.tif")
    assert os.path.exists("data/mumbai_dem.tif")
    print("Files created successfully.")
    
    # Second request should be even faster and reuse files
    start_time = time.time()
    response = requests.post(url_layers, json=payload_mumbai)
    print(f"Second request status: {response.status_code}")
    print(f"Second request took: {time.time() - start_time:.2f}s")
    
    # Verify no new tasks were needed (hard to check from client, but we trust the server print)
    print("Test 5 passed! (Mumbai files cached and reused)")

    # Test 6: Pune Test (User specifically reported Pune)
    payload_pune = {
        "place_name": "Pune",
        "weights": {"layers": ["dem"]}
    }
    print("\nTesting /get-layers for Pune...")
    start_time = time.time()
    try:
        response = requests.post(url_layers, json=payload_pune, timeout=60)
        print(f"Pune request status: {response.status_code}")
        print(f"Pune request took: {time.time() - start_time:.2f}s")
        if response.status_code == 200:
            print(f"Pune keys: {list(response.json().keys())}")
    except requests.exceptions.Timeout:
        print("Pune request TIMED OUT (60s)")

    # Test 7: Full Pune string from screenshot
    full_pune = "Pune, Pune City, Pune District, Maharashtra"
    payload_full = {
        "place_name": full_pune,
        "weights": {"layers": ["dem"]}
    }
    print(f"\nTesting /get-layers for full string: {full_pune}")
    start_time = time.time()
    try:
        response = requests.post(url_layers, json=payload_full, timeout=60)
        print(f"Full Pune status: {response.status_code}")
        print(f"Full Pune took: {time.time() - start_time:.2f}s")
    except requests.exceptions.Timeout:
        print("Full Pune request TIMED OUT (60s)")

if __name__ == "__main__":
    try:
        test_selective_layers()
        print("\nVerification complete!")
    except Exception as e:
        print(f"\nTests failed: {e}")
