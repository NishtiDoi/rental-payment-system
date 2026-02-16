from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def setup_payment_test_data():
    """
    Create necessary entities for payment testing:
    1. Create landlord user
    2. Create renter user  
    3. Create property
    4. Create lease
    5. Create bank accounts for both users
    """
    # Create landlord
    landlord_resp = client.post("/api/v1/users/", json={
        "email": f"landlord_{uuid.uuid4().hex[:8]}@test.com",
        "full_name": "Test Landlord",
        "role": "landlord"
    })
    if landlord_resp.status_code != 201:
        raise Exception(f"Failed to create landlord: {landlord_resp.json()}")
    landlord_id = landlord_resp.json()["id"]
    
    # Create renter
    renter_resp = client.post("/api/v1/users/", json={
        "email": f"renter_{uuid.uuid4().hex[:8]}@test.com",
        "full_name": "Test Renter",
        "role": "renter"
    })
    if renter_resp.status_code != 201:
        raise Exception(f"Failed to create renter: {renter_resp.json()}")
    renter_id = renter_resp.json()["id"]
    
    # Create property
    property_resp = client.post("/api/v1/properties/", json={
        "landlord_id": landlord_id,
        "address": "123 Test St",
        "city": "Test City",
        "state": "TC",
        "zip_code": "12345",
        "monthly_rent": "2500.00"
    })
    if property_resp.status_code != 201:
        raise Exception(f"Failed to create property: {property_resp.json()}")
    property_id = property_resp.json()["id"]
    
    # Create lease
    lease_resp = client.post("/api/v1/leases/", json={
        "property_id": property_id,
        "renter_id": renter_id,
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2026-01-01T00:00:00",
        "rent_amount": "2500.00",
        "due_day_of_month": 1
    })
    if lease_resp.status_code != 201:
        raise Exception(f"Failed to create lease: {lease_resp.json()}")
    lease_id = lease_resp.json()["id"]
    
    # Create bank account for landlord (payee)
    payee_account_resp = client.post("/api/v1/bank-accounts/", json={
        "user_id": landlord_id,
        "account_number_token": "1234",
        "routing_number": "111000007",
        "bank_name": "Test Bank"
    })
    if payee_account_resp.status_code != 201:
        raise Exception(f"Failed to create payee account: {payee_account_resp.json()}")
    payee_account_id = payee_account_resp.json()["id"]
    
    # Create bank account for renter (payer)
    payer_account_resp = client.post("/api/v1/bank-accounts/", json={
        "user_id": renter_id,
        "account_number_token": "5678",
        "routing_number": "111000008",
        "bank_name": "Renter Bank"
    })
    if payer_account_resp.status_code != 201:
        raise Exception(f"Failed to create payer account: {payer_account_resp.json()}")
    payer_account_id = payer_account_resp.json()["id"]
    
    return {
        "lease_id": lease_id,
        "payer_account_id": payer_account_id,
        "payee_account_id": payee_account_id
    }


def test_idempotency_prevents_duplicate_payments():
    """
    Test that using the same idempotency key twice
    returns the same transaction without creating a duplicate
    """
    
    # Setup: Create all necessary entities
    entities = setup_payment_test_data()
    
    # Use a unique idempotency key
    idempotency_key = str(uuid.uuid4())
    
    payment_data = {
        "idempotency_key": idempotency_key,
        "lease_id": entities["lease_id"],
        "payer_account_id": entities["payer_account_id"],
        "payee_account_id": entities["payee_account_id"],
        "amount": "2500.00",
        "payment_rail_type": "standard_ach"
    }
    
    # First request - should create transaction
    response1 = client.post("/api/v1/payments/", json=payment_data)
    print("First response:", response1.status_code)
    print("Response body:", response1.json())

    assert response1.status_code == 201, f"Expected 201, got {response1.status_code}: {response1.json()}"
    transaction1_id = response1.json()["id"]
    
    # Second request with SAME idempotency key - should return same transaction
    response2 = client.post("/api/v1/payments/", json=payment_data)
    assert response2.status_code == 201
    transaction2_id = response2.json()["id"]
    
    # Verify it's the SAME transaction
    assert transaction1_id == transaction2_id
    print("✅ Idempotency working - no duplicate created!")

def test_idempotency_via_header():
    """Test idempotency key passed via header"""
    
    # Setup: Create all necessary entities
    entities = setup_payment_test_data()
    
    idempotency_key = str(uuid.uuid4())
    
    payment_data = {
        "lease_id": entities["lease_id"],
        "payer_account_id": entities["payer_account_id"],
        "payee_account_id": entities["payee_account_id"],
        "amount": "2500.00"
    }
    
    headers = {"Idempotency-Key": idempotency_key}
    
    response1 = client.post(
        "/api/v1/payments/", 
        json=payment_data, 
        headers=headers
    )
    assert response1.status_code == 201, f"Expected 201, got {response1.status_code}: {response1.json()}"
    
    response2 = client.post(
        "/api/v1/payments/", 
        json=payment_data, 
        headers=headers
    )
    assert response2.status_code == 201
    
    assert response1.json()["id"] == response2.json()["id"]
    print("✅ Header-based idempotency working!")