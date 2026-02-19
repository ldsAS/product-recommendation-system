
import sys
import os
import json
from datetime import datetime
from fastapi.testclient import TestClient

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.main import app

client = TestClient(app)

def test_recommendations():
    print("Testing POST /api/v1/recommendations...")
    payload = {
        "member_code": "CU000001",
        "phone": "0912345678",
        "total_consumption": 1000.0,
        "accumulated_bonus": 100.0,
        "recent_purchases": ["P001", "P002"],
        "top_k": 5
    }
    try:
        response = client.post("/api/v1/recommendations", json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        else:
            print("Success!")
            # Try to parse JSON to ensure it's valid
            data = response.json()
            print("Response JSON parsed successfully.")
    except Exception as e:
        print(f"Exception: {e}")

def test_monitoring_realtime():
    print("\nTesting GET /api/v1/monitoring/realtime...")
    try:
        response = client.get("/api/v1/monitoring/realtime")
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        else:
            print("Success!")
    except Exception as e:
        print(f"Exception: {e}")

def test_monitoring_statistics():
    print("\nTesting GET /api/v1/monitoring/statistics...")
    try:
        response = client.get("/api/v1/monitoring/statistics")
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        else:
            print("Success!")
    except Exception as e:
        print(f"Exception: {e}")

def test_alerts():
    print("\nTesting GET /api/v1/monitoring/alerts...")
    try:
        response = client.get("/api/v1/monitoring/alerts")
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        else:
            print("Success!")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_recommendations()
    test_monitoring_realtime()
    test_monitoring_statistics()
    test_alerts()
