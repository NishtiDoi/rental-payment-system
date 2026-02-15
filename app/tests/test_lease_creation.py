from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_lease_flow():
    # 1. Create landlord
    landlord = client.post("/api/v1/users/", json={
        "email": "lndylrd2@somn.com",
        "full_name": "John Landlord",
        "role": "landlord"
    })
    print("STATUS:", landlord.status_code)
    print("RESPONSE:", landlord.json())

    assert landlord.status_code == 201
    landlord_id = landlord.json()["id"]
    
    # 2. Create property
    property_resp = client.post("/api/v1/properties/", json={
        "landlord_id": landlord_id,
        "address": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94102",
        "monthly_rent": "2500.00"
    })
    assert property_resp.status_code == 201
    property_id = property_resp.json()["id"]
    
    # 3. Create renter
    renter = client.post("/api/v1/users/", json={
        "email": "renter2@tester.com",
        "full_name": "Jane Renter",
        "role": "renter"
    })
    print("STATUS:", renter.status_code)
    print("RESPONSE:", renter.json())

    assert renter.status_code == 201
    renter_id = renter.json()["id"]
    
    # 4. Create lease
    lease = client.post("/api/v1/leases/", json={
        "property_id": property_id,
        "renter_id": renter_id,
        "start_date": "2025-03-01T00:00:00",
        "end_date": "2026-03-01T00:00:00",
        "rent_amount": "2500.00",
        "due_day_of_month": 1
    })
    assert lease.status_code == 201
    print("✅ Full lease creation flow works!")