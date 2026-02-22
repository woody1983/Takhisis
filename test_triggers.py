
import pytest
import sqlite3
import os
from app import app, init_db, get_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    db_path = 'test_triggers.db'
    
    import app as app_module
    original_db_path = app_module.DB_PATH
    app_module.DB_PATH = db_path
    
    with app.test_client() as client:
        with app.app_context():
            if os.path.exists(db_path):
                os.remove(db_path)
            init_db()
        yield client
    
    if os.path.exists(db_path):
        os.remove(db_path)
    app_module.DB_PATH = original_db_path

def test_delete_accessory_triggers_rematch(client):
    """Test that deleting an accessory triggers a re-match for work orders assigned to it"""
    # 1. Add accessory
    client.post("/api/accessories", json={"sku": "DELETE-ME", "location": "LOC-1"}, content_type="application/json")
    
    # 2. Add work order matching it
    resp = client.post("/api/work-orders", json={"sku": "DELETE-ME", "accessory_code": "partA", "quantity": 1}, content_type="application/json")
    order_id = resp.get_json()['id']
    assert resp.get_json()['match_status'] == 'matched'
    assert resp.get_json()['location'] == 'LOC-1'

    # 3. Get accessory ID
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM accessories WHERE sku = 'DELETE-ME'")
        acc_id = cursor.fetchone()[0]
        conn.close()

    # 4. Delete accessory
    client.delete(f"/api/accessories/{acc_id}")

    # 5. Check work order - should be 'new_one' if no other inventory
    # Currently this will only be 'new_one' because of the REMATCH ON READ.
    # We want to ensure it works even WITHOUT the rematch on read later.
    resp = client.get(f"/api/work-orders/{order_id}")
    data = resp.get_json()
    assert data['match_status'] == 'new_one'
    assert data['location'] is None

def test_update_accessory_location_triggers_update(client):
    """Test that updating an accessory's location updates the matched work orders"""
    # 1. Add accessory
    client.post("/api/accessories", json={"sku": "MOVE-ME", "location": "LOC-OLD"}, content_type="application/json")
    
    # 2. Add work order matching it
    resp = client.post("/api/work-orders", json={"sku": "MOVE-ME", "accessory_code": "partA", "quantity": 1}, content_type="application/json")
    order_id = resp.get_json()['id']
    assert resp.get_json()['location'] == 'LOC-OLD'

    # 3. Get accessory ID
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM accessories WHERE sku = 'MOVE-ME'")
        acc_id = cursor.fetchone()[0]
        conn.close()

    # 4. Update accessory location
    client.put(f"/api/accessories/{acc_id}", json={"location": "LOC-NEW", "new_remark": ""}, content_type="application/json")

    # 5. Check work order - should be updated to LOC-NEW
    resp = client.get(f"/api/work-orders/{order_id}")
    data = resp.get_json()
    assert data['location'] == 'LOC-NEW'
