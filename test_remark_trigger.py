import pytest
import sqlite3
import os
from app import app, get_db
import app as app_module

@pytest.fixture
def client():
    app.config["TESTING"] = True
    # Use a temporary database file for trigger testing 
    test_db = "test_trigger_remark.db"
    app.config["DATABASE"] = test_db
    app_module.DB_PATH = test_db
    
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS accessories")
        cursor.execute("DROP TABLE IF EXISTS remarks")
        cursor.execute("DROP TABLE IF EXISTS work_orders")
        cursor.execute("DROP TABLE IF EXISTS locations")
        
        cursor.execute("CREATE TABLE accessories (id INTEGER PRIMARY KEY, sku TEXT, location TEXT, updated_at TIMESTAMP)")
        cursor.execute("CREATE TABLE remarks (id INTEGER PRIMARY KEY, accessory_id INTEGER, content TEXT, created_at TIMESTAMP)")
        cursor.execute("CREATE TABLE work_orders (id INTEGER PRIMARY KEY, sku TEXT, accessory_code TEXT, quantity INTEGER, status TEXT DEFAULT 'pending', match_status TEXT, location TEXT, customer_service_name TEXT, remark TEXT)")
        cursor.execute("CREATE TABLE locations (name TEXT PRIMARY KEY, usage_count INTEGER DEFAULT 0)")
        conn.commit()
    
    with app.test_client() as client:
        yield client
        
    if os.path.exists(test_db):
        os.remove(test_db)

def test_remark_addition_triggers_rematch(client):
    # 1. Setup inventory: IRON at LOC-A
    client.post("/api/locations", json={"name": "LOC-A"})
    client.post("/api/accessories", json={"sku": "IRON", "location": "LOC-A"})
    
    # 2. Create Work Order for IRON/Part-C
    # Should automatically match to LOC-A
    resp = client.post("/api/work-orders", json={"sku": "IRON", "accessory_code": "Part-C", "quantity": 1})
    print(f"DEBUG: Response: {resp.status_code}, {resp.get_json()}")
    order_id = resp.get_json()["id"]
    
    # Verify it is matched
    resp = client.get(f"/api/work-orders/{order_id}")
    data = resp.get_json()
    assert data["match_status"] == "matched"
    assert data["location"] == "LOC-A"
    
    # 3. Update Accessory with remark "Part-C is missing"
    # Accessory ID should be 1
    client.put("/api/accessories/1", json={
        "location": "LOC-A", # same location
        "new_remark": "We found that Part-C is missing from the package."
    })
    
    # 4. ASSERTION: Work order should have been re-matched and find no stock
    resp = client.get(f"/api/work-orders/{order_id}")
    data = resp.get_json()
    
    # THIS IS EXPECTED TO FAIL BEFORE THE FIX
    assert data["match_status"] == "new_one", "Work order should be unmatched because the only item is now missing Part-C"
    assert data["location"] is None
