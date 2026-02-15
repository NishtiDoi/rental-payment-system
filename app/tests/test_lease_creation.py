from fastapi.testclient import TestClient
from app.main import app

client =TestClient(app)

def test_create_lease_flow():
    # 1. Create landlord
    landlord = client.post("/api/v1/users/", json={
        "email": "landlord@test.com",
        "full_name": "John Landlord",
        "role": "landlord"
    })
    assert landlord.status_code == 201
    landlord_id = landlord.json()["id"]