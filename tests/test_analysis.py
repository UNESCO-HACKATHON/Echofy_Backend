from fastapi.testclient import TestClient
from app.app import app

client = TestClient(app)

# Test valid content (should not be flagged)
def test_analyze_content_reliable():
    response = client.post(
        "/api/v1/analyze",
        json={"content": "This is a well-written, factual article about science."},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_potentially_misleading"] is False
    assert 0.0 <= data["confidence_score"] <= 1.0
    assert "reliable" in data["explanation"].lower()


# Test content with trigger words (should be flagged)
def test_analyze_content_misleading():
    response = client.post(
        "/api/v1/analyze",
        json={"content": "Shocking news! This is a fake and misleading story."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_potentially_misleading"] is True
    assert 0.0 <= data["confidence_score"] <= 1.0
    assert "emotionally charged" in data["explanation"].lower()


# Test too short content (should return 422)
def test_analyze_content_too_short():
    response = client.post("/api/v1/analyze", json={"content": "short"})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


# Test missing content field (should return 422)
def test_analyze_content_missing_field():
    response = client.post("/api/v1/analyze", json={})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
