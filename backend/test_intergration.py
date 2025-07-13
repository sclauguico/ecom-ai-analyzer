import requests

BASE_URL = "http://localhost:8000"
def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
def test_quick_insights():
    response = requests.get(f"{BASE_URL}/quick-insights")
    assert response.status_code == 200
    data = response.json()
    assert "insights" in data
    assert len(data["insights"]) > 0
def test_analyze_endpoint():
    query = "What are our top selling products?"
    response = requests.post(f"{BASE_URL}/analyze", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert "results" in data
    assert data["query"] == query
if __name__ == "__main__":
    # Make sure your API is running before running these tests
    test_health_endpoint()
    test_quick_insights() 
    test_analyze_endpoint()
    print("All integration tests passed!")