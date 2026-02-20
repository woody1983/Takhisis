"""
Test suite for Accessory Management System
TDD approach - tests first, then implementation
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime
from app import (
    app,
    init_db,
    get_db,
    get_all_locations,
    add_location,
    update_location_usage,
    get_all_skus,
    get_sku_statistics,
    generate_unique_sku,
)


@pytest.fixture
def client():
    """Create a test client with temporary database"""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    app.config["TESTING"] = True
    app.config["DB_PATH"] = db_path

    # Override the DB_PATH in app
    import app as app_module

    original_db_path = app_module.DB_PATH
    app_module.DB_PATH = db_path

    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)
    app_module.DB_PATH = original_db_path


@pytest.fixture
def db():
    """Get database connection for tests"""
    conn = get_db()
    yield conn
    conn.close()


class TestDatabaseOperations:
    """Test database initialization and basic operations"""

    def test_database_tables_created(self, client):
        """Test that all required tables are created"""
        conn = get_db()
        cursor = conn.cursor()

        # Check accessories table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='accessories'"
        )
        assert cursor.fetchone() is not None

        # Check remarks table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='remarks'"
        )
        assert cursor.fetchone() is not None

        # Check locations table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='locations'"
        )
        assert cursor.fetchone() is not None

        conn.close()


class TestLocationManagement:
    """Test location-related functions"""

    def test_add_location_success(self, client):
        """Test adding a new location successfully"""
        success, message = add_location("A-01-01")
        assert success is True
        assert "successfully" in message

    def test_add_location_duplicate(self, client):
        """Test adding a duplicate location fails"""
        # Add location first time
        add_location("A-01-02")

        # Try to add again
        success, message = add_location("A-01-02")
        assert success is False
        assert "already exists" in message

    def test_get_all_locations_empty(self, client):
        """Test getting locations when none exist"""
        locations = get_all_locations()
        assert locations == []

    def test_get_all_locations_sorted(self, client):
        """Test locations are sorted by usage count"""
        # Add locations
        add_location("A-01")
        add_location("B-02")
        add_location("C-03")

        # Update usage counts
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE locations SET usage_count = 5 WHERE name = 'B-02'")
        cursor.execute("UPDATE locations SET usage_count = 10 WHERE name = 'A-01'")
        conn.commit()
        conn.close()

        locations = get_all_locations()
        assert len(locations) == 3
        # Should be sorted by usage_count DESC
        assert locations[0]["name"] == "A-01"
        assert locations[1]["name"] == "B-02"
        assert locations[2]["name"] == "C-03"

    def test_update_location_usage(self, client):
        """Test incrementing location usage count"""
        add_location("A-01")

        # Update usage
        update_location_usage("A-01")

        # Check result
        locations = get_all_locations()
        assert locations[0]["usage_count"] == 1

        # Update again
        update_location_usage("A-01")
        locations = get_all_locations()
        assert locations[0]["usage_count"] == 2


class TestSKUFunctions:
    """Test SKU-related functions"""

    def test_get_all_skus_empty(self, client):
        """Test getting SKUs when no accessories exist"""
        skus = get_all_skus()
        assert skus == []

    def test_get_all_skus_sorted(self, client):
        """Test SKUs are returned sorted"""
        # Add accessories
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("SKU-B", "A-01")
        )
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("SKU-A", "A-01")
        )
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("SKU-C", "A-01")
        )
        conn.commit()
        conn.close()

        skus = get_all_skus()
        assert skus == ["SKU-A", "SKU-B", "SKU-C"]

    def test_get_sku_statistics_empty(self, client):
        """Test SKU statistics when no accessories exist"""
        stats = get_sku_statistics()
        assert stats == []

    def test_get_sku_statistics_grouping(self, client):
        """Test SKU statistics groups variants together"""
        # Add accessories with variants
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("ABC123", "A-01")
        )
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)",
            ("ABC123*1", "A-02"),
        )
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)",
            ("ABC123*2", "A-03"),
        )
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("XYZ789", "B-01")
        )
        conn.commit()
        conn.close()

        stats = get_sku_statistics()
        assert len(stats) == 2

        # ABC123 should have count 3 (including variants)
        abc_stat = next(s for s in stats if s[0] == "ABC123")
        assert abc_stat[1] == 3

        # XYZ789 should have count 1
        xyz_stat = next(s for s in stats if s[0] == "XYZ789")
        assert xyz_stat[1] == 1

    def test_get_sku_statistics_sorted(self, client):
        """Test SKU statistics are sorted by count descending"""
        conn = get_db()
        cursor = conn.cursor()
        # Add 5 of SKU-A, 3 of SKU-B, 10 of SKU-C
        for i in range(5):
            cursor.execute(
                "INSERT INTO accessories (sku, location) VALUES (?, ?)",
                (f"SKU-A", f"A-{i}"),
            )
        for i in range(3):
            cursor.execute(
                "INSERT INTO accessories (sku, location) VALUES (?, ?)",
                (f"SKU-B", f"B-{i}"),
            )
        for i in range(10):
            cursor.execute(
                "INSERT INTO accessories (sku, location) VALUES (?, ?)",
                (f"SKU-C", f"C-{i}"),
            )
        conn.commit()
        conn.close()

        stats = get_sku_statistics()
        assert stats[0][0] == "SKU-C"  # 10 items
        assert stats[1][0] == "SKU-A"  # 5 items
        assert stats[2][0] == "SKU-B"  # 3 items


class TestGenerateUniqueSKU:
    """Test SKU uniqueness generation"""

    def test_generate_unique_sku_no_duplicate(self, client):
        """Test SKU is returned as-is when no duplicate exists"""
        conn = get_db()
        cursor = conn.cursor()

        result = generate_unique_sku(cursor, "ABC123", "A-01")
        assert result == "ABC123"

        conn.close()

    def test_generate_unique_sku_first_duplicate(self, client):
        """Test first duplicate gets *1 suffix"""
        conn = get_db()
        cursor = conn.cursor()

        # Add first accessory
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("ABC123", "A-01")
        )
        conn.commit()

        # Generate unique SKU
        result = generate_unique_sku(cursor, "ABC123", "A-01")
        assert result == "ABC123*1"

        conn.close()

    def test_generate_unique_sku_multiple_duplicates(self, client):
        """Test multiple duplicates get sequential suffixes"""
        conn = get_db()
        cursor = conn.cursor()

        # Add accessories
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("ABC123", "A-01")
        )
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)",
            ("ABC123*1", "A-01"),
        )
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)",
            ("ABC123*2", "A-01"),
        )
        conn.commit()

        # Generate unique SKU
        result = generate_unique_sku(cursor, "ABC123", "A-01")
        assert result == "ABC123*3"

        conn.close()

    def test_generate_unique_sku_different_location(self, client):
        """Test same SKU at different location is allowed"""
        conn = get_db()
        cursor = conn.cursor()

        # Add at location A-01
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("ABC123", "A-01")
        )
        conn.commit()

        # Same SKU at different location should be allowed
        result = generate_unique_sku(cursor, "ABC123", "B-01")
        assert result == "ABC123"

        conn.close()


class TestFlaskRoutes:
    """Test Flask route handlers"""

    def test_index_route(self, client):
        """Test homepage loads successfully"""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Accessory Management" in response.data

    def test_index_route_with_pagination(self, client):
        """Test homepage with page parameter"""
        response = client.get("/?page=1")
        assert response.status_code == 200

    def test_add_accessory_success(self, client):
        """Test adding an accessory successfully"""
        # First add a location
        add_location("A-01")

        response = client.post(
            "/add", data={"sku": "TEST123", "location": "A-01", "remark": "Test remark"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_add_accessory_missing_sku(self, client):
        """Test adding accessory without SKU fails"""
        response = client.post(
            "/add", data={"sku": "", "location": "A-01", "remark": ""}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "required" in data["message"].lower()

    def test_add_accessory_missing_location(self, client):
        """Test adding accessory without location fails"""
        response = client.post(
            "/add", data={"sku": "TEST123", "location": "", "remark": ""}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "required" in data["message"].lower()

    def test_add_accessory_duplicate_sku(self, client):
        """Test adding duplicate SKU generates unique SKU"""
        add_location("A-01")

        # Add first accessory
        client.post("/add", data={"sku": "DUP123", "location": "A-01", "remark": ""})

        # Add duplicate
        response = client.post(
            "/add", data={"sku": "DUP123", "location": "A-01", "remark": ""}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "DUP123*1" in data["message"]

    def test_detail_route_exists(self, client):
        """Test detail page for existing accessory"""
        # Add location and accessory
        add_location("A-01")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("TEST123", "A-01")
        )
        accessory_id = cursor.lastrowid
        conn.commit()
        conn.close()

        response = client.get(f"/detail/{accessory_id}")
        assert response.status_code == 200
        assert b"TEST123" in response.data

    def test_detail_route_not_found(self, client):
        """Test detail page for non-existent accessory"""
        response = client.get("/detail/999")
        assert response.status_code == 404

    def test_delete_accessory(self, client):
        """Test deleting an accessory"""
        # Add location and accessory
        add_location("A-01")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("DEL123", "A-01")
        )
        accessory_id = cursor.lastrowid
        conn.commit()
        conn.close()

        response = client.post(f"/delete/{accessory_id}")
        assert response.status_code == 302  # Redirect

        # Verify deleted
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accessories WHERE id = ?", (accessory_id,))
        assert cursor.fetchone() is None
        conn.close()

    def test_locations_page(self, client):
        """Test locations management page"""
        response = client.get("/locations")
        assert response.status_code == 200
        assert b"Location Management" in response.data

    def test_add_location_route_success(self, client):
        """Test adding location via route"""
        response = client.post("/locations/add", data={"name": "NEW-LOC"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_add_location_route_duplicate(self, client):
        """Test adding duplicate location via route"""
        # Add first
        client.post("/locations/add", data={"name": "DUP-LOC"})

        # Try duplicate
        response = client.post("/locations/add", data={"name": "DUP-LOC"})
        assert response.status_code == 409
        data = response.get_json()
        assert data["success"] is False

    def test_api_skus(self, client):
        """Test API endpoint for SKUs"""
        # Add some data
        add_location("A-01")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("API-SKU", "A-01")
        )
        conn.commit()
        conn.close()

        response = client.get("/api/skus")
        assert response.status_code == 200
        data = response.get_json()
        assert "API-SKU" in data

    def test_api_locations(self, client):
        """Test API endpoint for locations"""
        add_location("API-LOC")

        response = client.get("/api/locations")
        assert response.status_code == 200
        data = response.get_json()
        assert any(loc["name"] == "API-LOC" for loc in data)

    def test_sku_detail_route(self, client):
        """Test SKU detail page"""
        # Add data
        add_location("A-01")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)",
            ("SKUDETAIL", "A-01"),
        )
        conn.commit()
        conn.close()

        response = client.get("/sku/SKUDETAIL")
        assert response.status_code == 200
        assert b"SKUDETAIL" in response.data


class TestUpdateAccessory:
    """Test updating accessories"""

    def test_update_location(self, client):
        """Test updating accessory location"""
        # Setup
        add_location("A-01")
        add_location("B-02")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("UPD123", "A-01")
        )
        accessory_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Update
        response = client.post(
            f"/update/{accessory_id}", data={"location": "B-02", "new_remark": ""}
        )

        assert response.status_code == 302  # Redirect

        # Verify
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT location FROM accessories WHERE id = ?", (accessory_id,))
        result = cursor.fetchone()
        assert result["location"] == "B-02"
        conn.close()

    def test_update_add_remark(self, client):
        """Test adding remark during update"""
        # Setup
        add_location("A-01")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("REM123", "A-01")
        )
        accessory_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Add remark
        response = client.post(
            f"/update/{accessory_id}",
            data={"location": "A-01", "new_remark": "New test remark"},
        )

        assert response.status_code == 302

        # Verify remark added
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM remarks WHERE accessory_id = ?", (accessory_id,))
        remark = cursor.fetchone()
        assert remark is not None
        assert remark["content"] == "New test remark"
        conn.close()


class TestDeleteRemark:
    """Test deleting remarks"""

    def test_delete_remark(self, client):
        """Test deleting a single remark"""
        # Setup
        add_location("A-01")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)", ("DELREM", "A-01")
        )
        accessory_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO remarks (accessory_id, content) VALUES (?, ?)",
            (accessory_id, "To be deleted"),
        )
        remark_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Delete remark
        response = client.post(f"/delete_remark/{remark_id}")
        assert response.status_code == 302

        # Verify deleted
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM remarks WHERE id = ?", (remark_id,))
        assert cursor.fetchone() is None
        conn.close()


class TestDeleteLocation:
    """Test deleting locations"""

    def test_delete_location(self, client):
        """Test deleting a location"""
        # Add location
        add_location("DEL-LOC")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM locations WHERE name = ?", ("DEL-LOC",))
        location_id = cursor.fetchone()["id"]
        conn.close()

        # Delete
        response = client.post(f"/locations/delete/{location_id}")
        assert response.status_code == 302

        # Verify
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM locations WHERE id = ?", (location_id,))
        assert cursor.fetchone() is None
        conn.close()


class TestWorkOrderSystem:
    """Test Work Order system functionality"""

    def test_create_work_order_success(self, client):
        """Test creating a work order successfully"""
        response = client.post(
            "/api/work-orders",
            json={
                "sku": "TEST-SKU-001",
                "accessory_code": "ACC-001",
                "quantity": 5,
                "customer_service_name": "Test User",
                "remark": "Test remark",
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "created" in data["message"].lower()

    def test_create_work_order_missing_required_fields(self, client):
        """Test creating work order without required fields fails"""
        # Missing SKU
        response = client.post(
            "/api/work-orders",
            json={"accessory_code": "ACC-001", "quantity": 5},
            content_type="application/json",
        )
        assert response.status_code == 400

        # Missing accessory_code
        response = client.post(
            "/api/work-orders",
            json={"sku": "TEST-SKU", "quantity": 5},
            content_type="application/json",
        )
        assert response.status_code == 400

        # Missing quantity
        response = client.post(
            "/api/work-orders",
            json={"sku": "TEST-SKU", "accessory_code": "ACC-001"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_work_order_invalid_quantity(self, client):
        """Test creating work order with invalid quantity"""
        response = client.post(
            "/api/work-orders",
            json={"sku": "TEST-SKU", "accessory_code": "ACC-001", "quantity": -1},
            content_type="application/json",
        )
        assert response.status_code == 400

        response = client.post(
            "/api/work-orders",
            json={"sku": "TEST-SKU", "accessory_code": "ACC-001", "quantity": 0},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_get_work_orders_empty(self, client):
        """Test getting work orders when none exist"""
        response = client.get("/api/work-orders")
        assert response.status_code == 200
        data = response.get_json()
        assert data["work_orders"] == []
        assert data["counts"]["pending"] == 0
        assert data["counts"]["completed"] == 0
        assert data["counts"]["cancelled"] == 0

    def test_get_work_orders_with_data(self, client):
        """Test getting work orders with existing data"""
        # Create some work orders and get their IDs
        response1 = client.post(
            "/api/work-orders",
            json={"sku": "SKU-1", "accessory_code": "ACC-1", "quantity": 1},
            content_type="application/json",
        )
        assert response1.status_code == 200

        response2 = client.post(
            "/api/work-orders",
            json={"sku": "SKU-2", "accessory_code": "ACC-2", "quantity": 2},
            content_type="application/json",
        )
        assert response2.status_code == 200

        response = client.get("/api/work-orders")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["work_orders"]) == 2
        assert data["counts"]["pending"] == 2

    def test_get_work_orders_filtered_by_status(self, client):
        """Test filtering work orders by status"""
        # Create work orders
        response1 = client.post(
            "/api/work-orders",
            json={"sku": "SKU-1", "accessory_code": "ACC-1", "quantity": 1},
            content_type="application/json",
        )
        assert response1.status_code == 200

        response2 = client.post(
            "/api/work-orders",
            json={"sku": "SKU-2", "accessory_code": "ACC-2", "quantity": 2},
            content_type="application/json",
        )
        assert response2.status_code == 200

        # Get the first work order ID
        response = client.get("/api/work-orders")
        data = response.get_json()
        first_order_id = data["work_orders"][0]["id"]

        # Complete one
        client.put(
            f"/api/work-orders/{first_order_id}",
            json={"status": "completed"},
            content_type="application/json",
        )

        # Get pending only
        response = client.get("/api/work-orders?status=pending")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["work_orders"]) == 1
        assert data["work_orders"][0]["status"] == "pending"

    def test_update_work_order_status(self, client):
        """Test updating work order status"""
        # Create work order
        response = client.post(
            "/api/work-orders",
            json={"sku": "TEST", "accessory_code": "ACC", "quantity": 1},
            content_type="application/json",
        )
        assert response.status_code == 200

        # Get the work order ID
        response = client.get("/api/work-orders")
        data = response.get_json()
        order_id = data["work_orders"][0]["id"]

        # Update to completed
        response = client.put(
            f"/api/work-orders/{order_id}",
            json={"status": "completed"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        # Verify
        response = client.get("/api/work-orders")
        data = response.get_json()
        # Find the completed order
        completed_orders = [
            w for w in data["work_orders"] if w["status"] == "completed"
        ]
        assert len(completed_orders) == 1
        assert completed_orders[0]["completed_at"] is not None

    def test_update_work_order_invalid_status(self, client):
        """Test updating work order with invalid status"""
        # Create work order
        client.post(
            "/api/work-orders",
            json={"sku": "TEST", "accessory_code": "ACC", "quantity": 1},
            content_type="application/json",
        )

        # Try invalid status
        response = client.put(
            "/api/work-orders/1",
            json={"status": "invalid_status"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_delete_work_order(self, client):
        """Test deleting a work order"""
        # Create work order
        response = client.post(
            "/api/work-orders",
            json={"sku": "TEST", "accessory_code": "ACC", "quantity": 1},
            content_type="application/json",
        )
        data = response.get_json()
        order_id = data["id"]

        # Delete using the actual order ID
        response = client.delete(f"/api/work-orders/{order_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        # Verify deleted
        response = client.get("/api/work-orders")
        data = response.get_json()
        assert len(data["work_orders"]) == 0

    def test_work_order_page_loads(self, client):
        """Test work orders page loads successfully"""
        response = client.get("/work-orders")
        assert response.status_code == 200
        assert b"Work Order Management" in response.data

    def test_work_order_status_sorting(self, client):
        """Test work orders are sorted by status (pending first)"""
        # Create work orders with different statuses
        # Order of creation: COMPLETED, PENDING, CANCELLED
        client.post(
            "/api/work-orders",
            json={"sku": "COMPLETED-1", "accessory_code": "ACC-1", "quantity": 1},
            content_type="application/json",
        )
        client.post(
            "/api/work-orders",
            json={"sku": "PENDING-1", "accessory_code": "ACC-2", "quantity": 1},
            content_type="application/json",
        )
        client.post(
            "/api/work-orders",
            json={"sku": "CANCELLED-1", "accessory_code": "ACC-3", "quantity": 1},
            content_type="application/json",
        )

        # Get all work orders to find their IDs
        response = client.get("/api/work-orders")
        data = response.get_json()

        # Find IDs by SKU
        completed_id = None
        cancelled_id = None
        for wo in data["work_orders"]:
            if wo["sku"] == "COMPLETED-1":
                completed_id = wo["id"]
            elif wo["sku"] == "CANCELLED-1":
                cancelled_id = wo["id"]

        # Complete the first one
        client.put(
            f"/api/work-orders/{completed_id}",
            json={"status": "completed"},
            content_type="application/json",
        )

        # Cancel the third one
        client.put(
            f"/api/work-orders/{cancelled_id}",
            json={"status": "cancelled"},
            content_type="application/json",
        )

        # Get work orders again
        response = client.get("/api/work-orders")
        data = response.get_json()

        # Check order: pending should be first
        assert data["work_orders"][0]["status"] == "pending"
        assert data["work_orders"][0]["sku"] == "PENDING-1"

    def test_work_order_pagination(self, client):
        """Test work order pagination"""
        # Create 15 work orders
        for i in range(15):
            response = client.post(
                "/api/work-orders",
                json={
                    "sku": f"SKU-{i}",
                    "accessory_code": f"ACC-{i}",
                    "quantity": 1,
                },
                content_type="application/json",
            )
            assert response.status_code == 200

        # Get page 1 (default 10 per page)
        response = client.get("/api/work-orders?page=1&per_page=10")
        assert response.status_code == 200
        data = response.get_json()

        assert len(data["work_orders"]) == 10
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 10
        assert data["pagination"]["total"] == 15
        assert data["pagination"]["total_pages"] == 2

        # Get page 2
        response = client.get("/api/work-orders?page=2&per_page=10")
        assert response.status_code == 200
        data = response.get_json()

        assert len(data["work_orders"]) == 5
        assert data["pagination"]["page"] == 2

    def test_work_order_pagination_with_status_filter(self, client):
        """Test pagination with status filter"""
        # Create work orders with different statuses
        for i in range(5):
            response = client.post(
                "/api/work-orders",
                json={
                    "sku": f"PENDING-{i}",
                    "accessory_code": f"ACC-{i}",
                    "quantity": 1,
                },
                content_type="application/json",
            )
            assert response.status_code == 200

        for i in range(3):
            response = client.post(
                "/api/work-orders",
                json={
                    "sku": f"COMPLETED-{i}",
                    "accessory_code": f"COMP-{i}",
                    "quantity": 1,
                },
                content_type="application/json",
            )
            assert response.status_code == 200

        # Get all work orders to find IDs of completed ones
        response = client.get("/api/work-orders")
        data = response.get_json()

        # Mark some as completed
        completed_count = 0
        for wo in data["work_orders"]:
            if wo["sku"].startswith("COMPLETED-") and completed_count < 3:
                client.put(
                    f"/api/work-orders/{wo['id']}",
                    json={"status": "completed"},
                    content_type="application/json",
                )
                completed_count += 1

        # Get only pending with pagination
        response = client.get("/api/work-orders?status=pending&page=1&per_page=3")
        assert response.status_code == 200
        data = response.get_json()

        assert len(data["work_orders"]) == 3
        assert all(w["status"] == "pending" for w in data["work_orders"])
        assert data["pagination"]["total"] == 5

    def test_work_orders_page_with_pagination(self, client):
        """Test work orders page renders with pagination"""
        # Create 12 work orders
        for i in range(12):
            client.post(
                "/api/work-orders",
                json={
                    "sku": f"SKU-{i}",
                    "accessory_code": f"ACC-{i}",
                    "quantity": 1,
                },
                content_type="application/json",
            )

        # Get page 1
        response = client.get("/work-orders")
        assert response.status_code == 200
        assert b"pagination" in response.data or b"Showing" in response.data

        # Get page 2
        response = client.get("/work-orders/page/2")
        assert response.status_code == 200


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_full_accessory_workflow(self, client):
        """Test complete accessory management workflow"""
        # 1. Add location
        client.post("/locations/add", data={"name": "A-01"})

        # 2. Add accessory
        response = client.post(
            "/add",
            data={
                "sku": "INTEGRATION-TEST",
                "location": "A-01",
                "remark": "Initial remark",
            },
        )
        assert response.get_json()["success"] is True

        # 3. Get accessory ID
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM accessories WHERE sku = ?", ("INTEGRATION-TEST",)
        )
        accessory_id = cursor.fetchone()["id"]
        conn.close()

        # 4. Update accessory
        response = client.post(
            f"/update/{accessory_id}",
            data={"location": "A-01", "new_remark": "Updated remark"},
        )
        assert response.status_code == 302

        # 5. Verify remarks (Initial remark + Updated remark = 2 remarks)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM remarks WHERE accessory_id = ?", (accessory_id,)
        )
        assert cursor.fetchone()[0] == 2
        conn.close()

        # 6. Delete accessory
        response = client.post(f"/delete/{accessory_id}")
        assert response.status_code == 302

        # 7. Verify deleted
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accessories WHERE id = ?", (accessory_id,))
        assert cursor.fetchone() is None
        conn.close()

    def test_full_work_order_workflow(self, client):
        """Test complete work order workflow"""
        # 1. Create work order
        response = client.post(
            "/api/work-orders",
            json={
                "sku": "WORKFLOW-TEST",
                "accessory_code": "WF-001",
                "quantity": 10,
                "customer_service_name": "Test Agent",
                "remark": "Urgent order",
            },
            content_type="application/json",
        )
        assert response.get_json()["success"] is True

        # 2. Get work order
        response = client.get("/api/work-orders")
        data = response.get_json()
        assert len(data["work_orders"]) == 1
        order_id = data["work_orders"][0]["id"]

        # 3. Update status to completed
        response = client.put(
            f"/api/work-orders/{order_id}",
            json={"status": "completed"},
            content_type="application/json",
        )
        assert response.get_json()["success"] is True

        # 4. Verify counts
        response = client.get("/api/work-orders")
        data = response.get_json()
        assert data["counts"]["completed"] == 1
        assert data["counts"]["pending"] == 0

        # 5. Delete work order
        response = client.delete(f"/api/work-orders/{order_id}")
        assert response.get_json()["success"] is True

        # 6. Verify deleted
        response = client.get("/api/work-orders")
        data = response.get_json()
        assert len(data["work_orders"]) == 0


class TestWorkOrderInventoryMatching:
    """Test Issue #17: Work Order automatic inventory matching"""

    def test_work_order_has_match_status_field(self, client):
        """Test that work order has match_status field in database"""
        # Create a work order
        response = client.post(
            "/api/work-orders",
            json={"sku": "TEST-SKU-001", "accessory_code": "ACC-001", "quantity": 5},
            content_type="application/json",
        )
        assert response.status_code == 200

        # Check the database schema includes match_status
        db_path = client.application.config.get("DB_PATH")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(work_orders)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        assert "match_status" in columns

    def test_work_order_id_is_6_digit_number(self, client):
        """Test that work order ID is a 6-digit random number"""
        response = client.post(
            "/api/work-orders",
            json={"sku": "TEST-SKU-002", "accessory_code": "ACC-002", "quantity": 3},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()

        # Check ID is a 6-digit number
        order_id = data["id"]
        assert isinstance(order_id, int)
        assert 100000 <= order_id <= 999999

        # Create another work order and verify ID is different
        response2 = client.post(
            "/api/work-orders",
            json={"sku": "TEST-SKU-003", "accessory_code": "ACC-003", "quantity": 2},
            content_type="application/json",
        )
        data2 = response2.get_json()
        order_id2 = data2["id"]

        # IDs should be different
        assert order_id != order_id2

    def test_create_work_order_auto_match_with_inventory(self, client):
        """Test creating work order auto-matches when SKU exists in inventory"""
        # First, add an accessory to inventory
        db_path = client.application.config.get("DB_PATH")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location) VALUES (?, ?)",
            ("MATCH-SKU-001", "A-01-01"),
        )
        conn.commit()
        conn.close()

        # Create work order with matching SKU
        response = client.post(
            "/api/work-orders",
            json={"sku": "MATCH-SKU-001", "accessory_code": "ACC-001", "quantity": 5},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["match_status"] == "matched"
        assert data["location"] == "A-01-01"

    def test_create_work_order_no_match_without_inventory(self, client):
        """Test creating work order shows 'new one' when SKU not in inventory"""
        # Create work order without matching SKU in inventory
        response = client.post(
            "/api/work-orders",
            json={"sku": "NO-MATCH-SKU", "accessory_code": "ACC-001", "quantity": 5},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["match_status"] == "new_one"
        assert "created" in data["message"].lower()

    def test_get_work_order_with_location_details(self, client):
        """Test getting work order details includes location info when matched"""
        # Add accessory to inventory
        db_path = client.application.config.get("DB_PATH")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location, updated_at) VALUES (?, ?, ?)",
            ("DETAIL-SKU-001", "B-02-03", datetime.now().isoformat()),
        )
        accessory_id = cursor.lastrowid

        # Add a remark to the accessory
        cursor.execute(
            "INSERT INTO remarks (accessory_id, content) VALUES (?, ?)",
            (accessory_id, "Test accessory details"),
        )
        conn.commit()
        conn.close()

        # Create work order
        response = client.post(
            "/api/work-orders",
            json={"sku": "DETAIL-SKU-001", "accessory_code": "ACC-002", "quantity": 3},
            content_type="application/json",
        )
        assert response.status_code == 200
        order_data = response.get_json()
        order_id = order_data.get("id")

        # Get work order details
        response = client.get(f"/api/work-orders/{order_id}")
        assert response.status_code == 200
        data = response.get_json()

        assert data["match_status"] == "matched"
        assert data["location"] == "B-02-03"
        assert "accessory_details" in data

    def test_work_order_match_status_pending_initially(self, client):
        """Test that match_status starts as pending before matching"""
        response = client.post(
            "/api/work-orders",
            json={"sku": "PENDING-SKU", "accessory_code": "ACC-001", "quantity": 1},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()

        # Should have match_status field
        assert "match_status" in data

    def test_create_work_order_with_removed_accessory_code(self, client):
        """Test that work order is marked as new_one when accessory_code has been removed"""
        # Add accessory to inventory
        db_path = client.application.config.get("DB_PATH")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location, updated_at) VALUES (?, ?, ?)",
            ("REMOVED-SKU-001", "A-01-01", datetime.now().isoformat()),
        )
        accessory_id = cursor.lastrowid

        # Add remove mark for partA
        cursor.execute(
            "INSERT INTO remarks (accessory_id, content, created_at) VALUES (?, ?, ?)",
            (
                accessory_id,
                "remove part A - WO#123456 - 2026-02-19 10:00:00",
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        # Create work order for partA - should be new_one
        response = client.post(
            "/api/work-orders",
            json={"sku": "REMOVED-SKU-001", "accessory_code": "partA", "quantity": 1},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["match_status"] == "new_one"

    def test_create_work_order_with_spaced_accessory_code(self, client):
        """Test matching with spaced accessory_code format (e.g., 'part A' vs 'partA')"""
        # Add accessory to inventory
        db_path = client.application.config.get("DB_PATH")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location, updated_at) VALUES (?, ?, ?)",
            ("SPACED-SKU-001", "B-02-02", datetime.now().isoformat()),
        )
        accessory_id = cursor.lastrowid

        # Add remove mark with space: "remove part 1"
        cursor.execute(
            "INSERT INTO remarks (accessory_id, content, created_at) VALUES (?, ?, ?)",
            (
                accessory_id,
                "remove part 1 - WO#111111 - 2026-02-19 11:00:00",
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        # Create work order for "part1" (no space) - should match "remove part 1" (with space)
        response = client.post(
            "/api/work-orders",
            json={"sku": "SPACED-SKU-001", "accessory_code": "part1", "quantity": 1},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        # Should be new_one because "part1" matches "part 1" when normalized
        assert data["match_status"] == "new_one"

    def test_complete_work_order_adds_remove_mark(self, client):
        """Test that completing a work order adds remove mark to accessory"""
        # Add accessory to inventory
        db_path = client.application.config.get("DB_PATH")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location, updated_at) VALUES (?, ?, ?)",
            ("COMPLETE-SKU-001", "C-03-03", datetime.now().isoformat()),
        )
        accessory_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Create work order
        response = client.post(
            "/api/work-orders",
            json={"sku": "COMPLETE-SKU-001", "accessory_code": "partX", "quantity": 2},
            content_type="application/json",
        )
        assert response.status_code == 200
        order_data = response.get_json()
        order_id = order_data.get("id")
        assert order_data["match_status"] == "matched"

        # Complete the work order
        response = client.put(
            f"/api/work-orders/{order_id}",
            json={"status": "completed"},
            content_type="application/json",
        )
        assert response.status_code == 200

        # Verify remove mark was added
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT content FROM remarks WHERE accessory_id = ? ORDER BY created_at DESC LIMIT 1",
            (accessory_id,),
        )
        remark = cursor.fetchone()
        conn.close()

        assert remark is not None
        assert "partX" in remark[0]
        assert f"WO#{order_id}" in remark[0]

    def test_work_order_detail_page_shows_all_remarks(self, client):
        """Test that work order detail page shows all accessory remarks"""
        # Add accessory with multiple remarks
        db_path = client.application.config.get("DB_PATH")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accessories (sku, location, updated_at) VALUES (?, ?, ?)",
            ("MULTI-REMARK-SKU", "D-04-04", datetime.now().isoformat()),
        )
        accessory_id = cursor.lastrowid

        # Add multiple remarks
        cursor.execute(
            "INSERT INTO remarks (accessory_id, content, created_at) VALUES (?, ?, ?)",
            (accessory_id, "First remark", datetime.now().isoformat()),
        )
        cursor.execute(
            "INSERT INTO remarks (accessory_id, content, created_at) VALUES (?, ?, ?)",
            (accessory_id, "Second remark", datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

        # Create work order
        response = client.post(
            "/api/work-orders",
            json={"sku": "MULTI-REMARK-SKU", "accessory_code": "partY", "quantity": 1},
            content_type="application/json",
        )
        assert response.status_code == 200
        order_data = response.get_json()

        # Access work order detail page
        response = client.get(f"/work-orders/{order_data['id']}")
        assert response.status_code == 200

        # Check that page contains remarks section
        html = response.data.decode("utf-8")
        assert "Remark History" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
