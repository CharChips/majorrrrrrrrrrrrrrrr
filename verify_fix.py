import requests
import json

BASE_URL = "http://127.0.0.1:8000"
BAD_LOCATION = "Risk Care Hospital and Iccu, Thane, Shastri Nagar Road, Kranti Nagar"

def test_run_analysis_failure():
    print(f"Testing /run-analysis with bad location: {BAD_LOCATION}")
    payload = {
        "query": "hospitals",
        "place_name": BAD_LOCATION,
        "top_n": 5
    }
    try:
        response = requests.post(f"{BASE_URL}/run-analysis", json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 404:
            print("SUCCESS: Received 404 for invalid location.")
        else:
            print(f"FAILURE: Received {response.status_code} instead of 404.")
    except Exception as e:
        print(f"ERROR: {e}")

def test_get_layers_failure():
    print(f"\nTesting /get-layers with bad location: {BAD_LOCATION}")
    payload = {
        "place_name": BAD_LOCATION
    }
    try:
        response = requests.post(f"{BASE_URL}/get-layers", json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 404:
            print("SUCCESS: Received 404 for invalid location.")
        else:
            print(f"FAILURE: Received {response.status_code} instead of 404.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_run_analysis_failure()
    test_get_layers_failure()
