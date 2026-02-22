#!/usr/bin/env python3
"""
Accessory Management System - API Version
Features: REST API for React Frontend
Data Storage: SQLite Database
"""

import sqlite3
import json
import random
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    send_from_directory,
)
from flask_cors import CORS
import os


def generate_work_order_id():
    """Generate a random 6-digit work order ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    while True:
        # Generate random 6-digit number (100000-999999)
        new_id = random.randint(100000, 999999)

        # Check if ID already exists
        cursor.execute("SELECT id FROM work_orders WHERE id = ?", (new_id,))
        if cursor.fetchone() is None:
            conn.close()
            return new_id


app = Flask(__name__, static_folder="frontend/dist", static_url_path="")
CORS(app)  # Enable CORS for React frontend
DB_PATH = "accessories.db"


def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create accessories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accessories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            location TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create remarks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS remarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            accessory_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (accessory_id) REFERENCES accessories(id) ON DELETE CASCADE
        )
    """)

    # Create locations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            usage_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create work_orders table with 6-digit random ID
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY,
            sku TEXT NOT NULL,
            accessory_code TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            match_status TEXT DEFAULT 'pending',
            location TEXT,
            customer_service_name TEXT,
            remark TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================== API Routes ====================


@app.route("/api/accessories", methods=["GET"])
def api_get_accessories():
    """Get all accessories with pagination"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 7, type=int)
    offset = (page - 1) * per_page

    conn = get_db()
    cursor = conn.cursor()

    # Get total count
    cursor.execute("SELECT COUNT(*) as total FROM accessories")
    total = cursor.fetchone()["total"]

    # Get accessories for current page
    cursor.execute(
        """
        SELECT a.*, 
               (SELECT content FROM remarks 
                WHERE accessory_id = a.id 
                ORDER BY created_at DESC LIMIT 1) as latest_remark
        FROM accessories a
        ORDER BY a.updated_at DESC
        LIMIT ? OFFSET ?
    """,
        (per_page, offset),
    )

    accessories = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(
        {
            "accessories": accessories,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }
    )


def force_rematch_all_pending_orders(cursor):
    """
    Force a re-match for all pending work orders to ensure their match_status
    is up-to-date with the current inventory state.
    """
    # Get all pending work orders
    cursor.execute(
        "SELECT id, sku, accessory_code, match_status, location FROM work_orders WHERE status = 'pending'"
    )
    pending_orders = cursor.fetchall()

    for order in pending_orders:
        order_id = order["id"]
        sku = order["sku"]
        accessory_code = order["accessory_code"]
        current_match_status = order["match_status"]
        current_location = order["location"]

        # Find the best available match right now
        new_match = find_available_accessory(cursor, sku, accessory_code)

        if new_match:
            new_location = new_match["location"]
            # If the order was 'new_one' or if the location has changed, update it
            if current_match_status != "matched" or current_location != new_location:
                cursor.execute(
                    "UPDATE work_orders SET match_status = 'matched', location = ? WHERE id = ?",
                    (new_location, order_id),
                )
        else:
            # If no match is found, ensure the status is 'new_one'
            if current_match_status != "new_one":
                cursor.execute(
                    "UPDATE work_orders SET match_status = 'new_one', location = NULL WHERE id = ?",
                    (order_id,),
                )


@app.route("/api/accessories", methods=["POST"])
def api_add_accessory():
    """Add new accessory"""
    data = request.get_json()
    sku = data.get("sku", "").strip()
    location = data.get("location", "").strip()
    remark = data.get("remark", "").strip()

    if not sku or not location:
        return jsonify(
            {"success": False, "message": "SKU and Location are required"}
        ), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Generate unique SKU
        final_sku = generate_unique_sku(cursor, sku, location)

        # Insert accessory
        cursor.execute(
            """
            INSERT INTO accessories (sku, location, updated_at)
            VALUES (?, ?, ?)
        """,
            (final_sku, location, datetime.now()),
        )

        accessory_id = cursor.lastrowid

        # Update location usage count
        cursor.execute(
            """
            UPDATE locations SET usage_count = usage_count + 1 WHERE name = ?
        """,
            (location,),
        )

        # Insert remark if provided
        if remark:
            cursor.execute(
                """
                INSERT INTO remarks (accessory_id, content, created_at)
                VALUES (?, ?, ?)
            """,
                (accessory_id, remark, datetime.now()),
            )

        # After adding, check if any 'new_one' work orders can now be matched
        # Use the original SKU, not the potentially modified final_sku
        re_match_new_one_work_orders(cursor, sku)

        conn.commit()
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": f"Added successfully{' (SKU: ' + final_sku + ')' if final_sku != sku else ''}",
            }
        )
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/accessories/<int:id>", methods=["GET"])
def api_get_accessory(id):
    """Get accessory details"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM accessories WHERE id = ?", (id,))
    accessory = cursor.fetchone()

    if not accessory:
        conn.close()
        return jsonify({"error": "Accessory not found"}), 404

    # Get remarks
    cursor.execute(
        """
        SELECT * FROM remarks 
        WHERE accessory_id = ? 
        ORDER BY created_at DESC
    """,
        (id,),
    )
    remarks = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({"accessory": dict(accessory), "remarks": remarks})


def re_match_new_one_work_orders(cursor, sku):
    """After adding a new accessory, re-match work orders waiting for it."""
    # Find pending work orders that need this SKU and are marked as 'new_one'
    cursor.execute(
        """
        SELECT id, accessory_code FROM work_orders
        WHERE status = 'pending'
          AND match_status = 'new_one'
          AND sku = ?
    """,
        (sku,),
    )
    eligible_orders = cursor.fetchall()

    for order in eligible_orders:
        order_id = order["id"]
        accessory_code = order["accessory_code"]

        # Try to find an available accessory for this work order
        match = find_available_accessory(cursor, sku, accessory_code)

        if match:
            # If a match is found, update the work order
            new_location = match["location"]
            cursor.execute(
                """
                UPDATE work_orders 
                SET match_status = 'matched', location = ? 
                WHERE id = ?
            """,
                (new_location, order_id),
            )


@app.route("/api/accessories/<int:id>", methods=["PUT"])
def api_update_accessory(id):
    """Update accessory"""
    data = request.get_json()
    location = data.get("location", "").strip()
    new_remark = data.get("new_remark", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Update location and timestamp
        cursor.execute(
            """
            UPDATE accessories 
            SET location = ?, updated_at = ?
            WHERE id = ?
        """,
            (location, datetime.now(), id),
        )

        # Add new remark if provided
        if new_remark:
            cursor.execute(
                """
                INSERT INTO remarks (accessory_id, content, created_at)
                VALUES (?, ?, ?)
            """,
                (id, new_remark, datetime.now()),
            )

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Updated successfully"})
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/accessories/<int:id>", methods=["DELETE"])
def api_delete_accessory(id):
    """Delete accessory"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM accessories WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Deleted successfully"})
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/locations", methods=["GET"])
def api_get_locations():
    """Get all locations"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM locations ORDER BY usage_count DESC, name ASC")
    locations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(locations)


@app.route("/api/locations", methods=["POST"])
def api_add_location():
    """Add new location"""
    data = request.get_json()
    name = data.get("name", "").strip()

    if not name:
        return jsonify({"success": False, "message": "Location name is required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO locations (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Location added successfully"})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "message": "Location already exists"}), 409


@app.route("/api/locations/<int:id>", methods=["DELETE"])
def api_delete_location(id):
    """Delete location"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM locations WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Location deleted successfully"})
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/skus", methods=["GET"])
def api_get_skus():
    """Get all unique SKUs"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT sku FROM accessories ORDER BY sku")
    skus = [row["sku"] for row in cursor.fetchall()]
    conn.close()
    return jsonify(skus)


@app.route("/api/sku-stats", methods=["GET"])
def api_get_sku_stats():
    """Get SKU statistics"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT sku FROM accessories")

    sku_counts = {}
    for row in cursor.fetchall():
        sku = row["sku"]
        base_sku = sku.split("*")[0] if "*" in sku else sku
        sku_counts[base_sku] = sku_counts.get(base_sku, 0) + 1

    conn.close()

    sorted_stats = sorted(sku_counts.items(), key=lambda x: x[1], reverse=True)
    return jsonify(sorted_stats)


@app.route("/api/sku/<sku>", methods=["GET"])
def api_get_sku_detail(sku):
    """Get accessories for specific SKU"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT a.*, 
               (SELECT content FROM remarks 
                WHERE accessory_id = a.id 
                ORDER BY created_at DESC LIMIT 1) as latest_remark
        FROM accessories a
        WHERE a.sku = ? OR a.sku LIKE ?
        ORDER BY a.location
    """,
        (sku, f"{sku}*%"),
    )

    accessories = [dict(row) for row in cursor.fetchall()]
    locations = list(set([a["location"] for a in accessories]))

    conn.close()

    return jsonify(
        {
            "base_sku": sku,
            "accessories": accessories,
            "locations": sorted(locations),
            "total_count": len(accessories),
        }
    )


@app.route("/api/work-orders", methods=["GET"])
def api_get_work_orders():
    """Get all work orders with status sorting and pagination"""
    status = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Validate pagination parameters
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 10
    if per_page > 100:
        per_page = 100

    offset = (page - 1) * per_page

    conn = get_db()
    cursor = conn.cursor()

    # ===== Force re-match for all pending orders before fetching =====
    force_rematch_all_pending_orders(cursor)
    conn.commit()  # Commit any changes from the re-match
    # =================================================================

    # Build query with status priority: pending > completed > cancelled
    if status == "all":
        # Get total count first
        cursor.execute("SELECT COUNT(*) FROM work_orders")
        total = cursor.fetchone()[0]

        # Then get work orders sorted by status priority (pending first), then by created_at DESC
        # Exclude location and customer_service_name from list view
        cursor.execute(
            """
            SELECT id, sku, accessory_code, quantity, status, match_status, remark, created_at, completed_at 
            FROM work_orders 
            ORDER BY 
                CASE status 
                    WHEN 'pending' THEN 1 
                    WHEN 'completed' THEN 2 
                    WHEN 'cancelled' THEN 3 
                    ELSE 4 
                END,
                created_at DESC
            LIMIT ? OFFSET ?
            """,
            (per_page, offset),
        )
    else:
        # Get total count for this status first
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = ?", (status,))
        total = cursor.fetchone()[0]

        # Then get work orders
        # Exclude location and customer_service_name from list view
        cursor.execute(
            """
            SELECT id, sku, accessory_code, quantity, status, match_status, remark, created_at, completed_at 
            FROM work_orders 
            WHERE status = ? 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (status, per_page, offset),
        )

    work_orders = [dict(row) for row in cursor.fetchall()]

    # Get counts for all statuses
    cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'pending'")
    pending_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'completed'")
    completed_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'cancelled'")
    cancelled_count = cursor.fetchone()[0]

    conn.close()

    total_pages = (total + per_page - 1) // per_page

    return jsonify(
        {
            "work_orders": work_orders,
            "counts": {
                "pending": pending_count,
                "completed": completed_count,
                "cancelled": cancelled_count,
            },
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }
    )


def find_available_accessory(cursor, sku, accessory_code):
    """Find an available accessory for a given SKU and accessory_code, including variants."""
    # Find accessories matching the base SKU or its variants (e.g., SKU*1)
    cursor.execute(
        "SELECT id, location FROM accessories WHERE sku = ? OR sku LIKE ? ORDER BY updated_at DESC",
        (sku, f"{sku}*%"),
    )
    inventory_matches = cursor.fetchall()

    if not inventory_matches:
        return None

    import re

    normalized_code = accessory_code.replace(" ", "").lower()

    for accessory in inventory_matches:
        accessory_id = accessory["id"]
        cursor.execute(
            "SELECT content FROM remarks WHERE accessory_id = ? ORDER BY created_at DESC",
            (accessory_id,),
        )
        remarks = cursor.fetchall()
        is_removed = False
        for remark_row in remarks:
            content = remark_row["content"]
            if content:
                remove_patterns = re.findall(
                    r"remove\s+(.*?)(?:\s+-|\s*$|\s*\n)", content, re.IGNORECASE
                )
                for removed_item in remove_patterns:
                    normalized_removed = removed_item.replace(" ", "").lower()
                    if normalized_removed == normalized_code:
                        is_removed = True
                        break
            if is_removed:
                break

        if not is_removed:
            return accessory  # Return the matched accessory object

    return None


@app.route("/api/work-orders", methods=["POST"])
def api_add_work_order():
    """Add new work order with automatic inventory matching"""
    data = request.get_json()
    sku = data.get("sku", "").strip()
    accessory_code = data.get("accessory_code", "").strip()
    quantity = data.get("quantity", 0)
    customer_service_name = data.get("customer_service_name", "").strip()
    remark = data.get("remark", "").strip()

    if not sku or not accessory_code or not quantity:
        return jsonify(
            {
                "success": False,
                "message": "SKU, accessory code, and quantity are required",
            }
        ), 400

    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify(
                {"success": False, "message": "Quantity must be greater than 0"}
            ), 400
    except ValueError:
        return jsonify(
            {"success": False, "message": "Quantity must be a valid number"}
        ), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        matched_accessory = find_available_accessory(cursor, sku, accessory_code)

        match_status = "new_one"
        location = None
        if matched_accessory:
            match_status = "matched"
            location = matched_accessory["location"]

        message = "Work order created successfully"
        order_id = generate_work_order_id()

        cursor.execute(
            """
            INSERT INTO work_orders (id, sku, accessory_code, quantity, match_status, location, customer_service_name, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                order_id,
                sku,
                accessory_code,
                quantity,
                match_status,
                location,
                customer_service_name,
                remark,
            ),
        )

        conn.commit()
        conn.close()

        response_data = {
            "success": True,
            "message": message,
            "id": order_id,
            "match_status": match_status,
        }

        if location:
            response_data["location"] = location

        return jsonify(response_data)
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500


def re_match_pending_work_orders(cursor, sku, accessory_code, old_location):
    """Re-match pending work orders that were matched to a now-used accessory"""
    # Find other pending work orders that were matched to the same accessory
    cursor.execute(
        """
        SELECT id FROM work_orders
        WHERE status = 'pending'
          AND match_status = 'matched'
          AND sku = ?
          AND accessory_code = ?
          AND location = ?
    """,
        (sku, accessory_code, old_location),
    )
    affected_orders = cursor.fetchall()

    for order in affected_orders:
        order_id = order["id"]
        # Try to find a new available accessory
        new_match = find_available_accessory(cursor, sku, accessory_code)

        if new_match:
            # If a new match is found, update the work order
            new_location = new_match["location"]
            cursor.execute(
                "UPDATE work_orders SET location = ? WHERE id = ?",
                (new_location, order_id),
            )
        else:
            # If no new match is found, update status to 'new_one'
            cursor.execute(
                "UPDATE work_orders SET match_status = 'new_one', location = NULL WHERE id = ?",
                (order_id,),
            )


@app.route("/api/work-orders/<int:id>", methods=["PUT"])
def api_update_work_order(id):
    """Update work order status"""
    data = request.get_json()
    status = data.get("status", "").strip()

    if status not in ["pending", "completed", "cancelled"]:
        return jsonify({"success": False, "message": "Invalid status"}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Get work order details first
        cursor.execute(
            "SELECT sku, accessory_code, location, match_status FROM work_orders WHERE id = ?",
            (id,),
        )
        work_order = cursor.fetchone()

        if status == "completed" and work_order:
            # Update work order status
            cursor.execute(
                """
                UPDATE work_orders 
                SET status = ?, completed_at = ?
                WHERE id = ?
            """,
                (status, datetime.now(), id),
            )

            # If matched to an accessory, add remove mark to the accessory's remarks
            if work_order["match_status"] == "matched" and work_order["location"]:
                # Find the accessory that was matched
                cursor.execute(
                    "SELECT id FROM accessories WHERE sku = ? AND location = ?",
                    (work_order["sku"], work_order["location"]),
                )
                accessory = cursor.fetchone()

                if accessory:
                    # Add remove mark to remarks
                    remove_mark = f"remove {work_order['accessory_code']} - WO#{id} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    cursor.execute(
                        """
                        INSERT INTO remarks (accessory_id, content, created_at)
                        VALUES (?, ?, ?)
                    """,
                        (accessory["id"], remove_mark, datetime.now()),
                    )

                # After completing a matched order, re-match other pending orders
                re_match_pending_work_orders(
                    cursor,
                    work_order["sku"],
                    work_order["accessory_code"],
                    work_order["location"],
                )
        else:
            cursor.execute(
                """
                UPDATE work_orders 
                SET status = ?, completed_at = NULL
                WHERE id = ?
            """,
                (status, id),
            )

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Work order updated successfully"})
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/work-orders/<int:id>", methods=["GET"])
def api_get_work_order(id):
    """Get single work order details with inventory info"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Force a re-match on this specific order before displaying
        cursor.execute(
            "SELECT status, sku, accessory_code, match_status, location FROM work_orders WHERE id = ? AND status = 'pending'",
            (id,),
        )
        order_to_check = cursor.fetchone()

        if order_to_check:
            new_match = find_available_accessory(
                cursor, order_to_check["sku"], order_to_check["accessory_code"]
            )
            if new_match:
                if (
                    order_to_check["match_status"] != "matched"
                    or order_to_check["location"] != new_match["location"]
                ):
                    cursor.execute(
                        "UPDATE work_orders SET match_status = 'matched', location = ? WHERE id = ?",
                        (new_match["location"], id),
                    )
                    conn.commit()
            else:
                if order_to_check["match_status"] != "new_one":
                    cursor.execute(
                        "UPDATE work_orders SET match_status = 'new_one', location = NULL WHERE id = ?",
                        (id,),
                    )
                    conn.commit()

        # Get work order details
        cursor.execute(
            """
            SELECT * FROM work_orders WHERE id = ?
        """,
            (id,),
        )
        order = cursor.fetchone()

        if not order:
            conn.close()
            return jsonify({"success": False, "message": "Work order not found"}), 404

        order_dict = dict(order)

        # If matched, get accessory details
        if order_dict.get("match_status") == "matched":
            cursor.execute(
                """
                SELECT a.*, r.content as latest_remark 
                FROM accessories a
                LEFT JOIN remarks r ON a.id = r.accessory_id
                WHERE a.sku = ?
                ORDER BY r.created_at DESC
                LIMIT 1
            """,
                (order_dict["sku"],),
            )
            accessory = cursor.fetchone()
            if accessory:
                order_dict["accessory_details"] = dict(accessory)

        conn.close()
        return jsonify(order_dict)
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/work-orders/<int:id>", methods=["DELETE"])
def api_delete_work_order(id):
    """Delete work order"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM work_orders WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Work order deleted successfully"})
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500


# ==================== Helper Functions ====================


def get_all_locations():
    """Get all locations sorted by usage count"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM locations ORDER BY usage_count DESC, name ASC")
    locations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return locations


def add_location(name):
    """Add a new location"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO locations (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return True, "Location added successfully"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Location already exists"


def update_location_usage(location_name):
    """Increment usage count for a location"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE locations SET usage_count = usage_count + 1 WHERE name = ?",
        (location_name,),
    )
    conn.commit()
    conn.close()


def get_all_skus():
    """Get all unique SKUs sorted alphabetically"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT sku FROM accessories ORDER BY sku")
    skus = [row["sku"] for row in cursor.fetchall()]
    conn.close()
    return skus


def get_sku_statistics():
    """Get SKU statistics grouped by base SKU"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT sku FROM accessories")

    sku_counts = {}
    for row in cursor.fetchall():
        sku = row["sku"]
        base_sku = sku.split("*")[0] if "*" in sku else sku
        sku_counts[base_sku] = sku_counts.get(base_sku, 0) + 1

    conn.close()

    sorted_stats = sorted(sku_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_stats


def generate_unique_sku(cursor, sku, location):
    """Generate unique SKU, append *1, *2, etc. if duplicate"""
    cursor.execute(
        "SELECT sku FROM accessories WHERE sku = ? AND location = ?", (sku, location)
    )

    if not cursor.fetchone():
        return sku

    cursor.execute(
        "SELECT sku FROM accessories WHERE (sku = ? OR sku LIKE ?) AND location = ?",
        (sku, f"{sku}*%", location),
    )

    existing_skus = [row[0] for row in cursor.fetchall()]

    max_num = 0
    for existing_sku in existing_skus:
        if existing_sku == sku:
            max_num = max(max_num, 1)
        elif "*" in existing_sku:
            try:
                num = int(existing_sku.split("*")[-1])
                max_num = max(max_num, num + 1)
            except ValueError:
                pass

    if max_num == 0:
        return f"{sku}*1"
    else:
        return f"{sku}*{max_num}"


# ==================== React Frontend Routes ====================


@app.route("/")
@app.route("/page/<int:page>")
def index(page=1):
    """Render homepage with accessories list"""
    per_page = 7
    offset = (page - 1) * per_page

    conn = get_db()
    cursor = conn.cursor()

    # Get total count
    cursor.execute("SELECT COUNT(*) as total FROM accessories")
    total = cursor.fetchone()["total"]
    total_pages = (total + per_page - 1) // per_page

    # Get accessories for current page
    cursor.execute(
        """
        SELECT a.*, 
               (SELECT content FROM remarks 
                WHERE accessory_id = a.id 
                ORDER BY created_at DESC LIMIT 1) as latest_remark
        FROM accessories a
        ORDER BY a.updated_at DESC
        LIMIT ? OFFSET ?
    """,
        (per_page, offset),
    )
    accessories = [dict(row) for row in cursor.fetchall()]

    # Get all SKUs for autocomplete
    cursor.execute("SELECT DISTINCT sku FROM accessories ORDER BY sku")
    skus = [row["sku"] for row in cursor.fetchall()]

    # Get all locations
    cursor.execute("SELECT * FROM locations ORDER BY usage_count DESC, name ASC")
    locations = [dict(row) for row in cursor.fetchall()]

    # Get SKU stats
    cursor.execute("SELECT sku FROM accessories")
    sku_counts = {}
    for row in cursor.fetchall():
        sku = row["sku"]
        base_sku = sku.split("*")[0] if "*" in sku else sku
        sku_counts[base_sku] = sku_counts.get(base_sku, 0) + 1
    sku_stats = sorted(sku_counts.items(), key=lambda x: x[1], reverse=True)

    conn.close()

    # Calculate pagination range
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)

    return render_template(
        "index.html",
        accessories=accessories,
        skus=skus,
        locations=locations,
        sku_stats=sku_stats,
        page=page,
        total_pages=total_pages,
        total=total,
        total_items=total,
        start_page=start_page,
        end_page=end_page,
    )


@app.route("/work-orders")
@app.route("/work-orders/page/<int:page>")
def work_orders_page(page=1):
    """Render work orders page with pagination and status sorting"""
    per_page = 10
    offset = (page - 1) * per_page

    conn = get_db()
    cursor = conn.cursor()

    # Get work orders sorted by status priority (pending first), then by created_at DESC
    cursor.execute(
        """
        SELECT * FROM work_orders 
        ORDER BY 
            CASE status 
                WHEN 'pending' THEN 1 
                WHEN 'completed' THEN 2 
                WHEN 'cancelled' THEN 3 
                ELSE 4 
            END,
            created_at DESC
        LIMIT ? OFFSET ?
        """,
        (per_page, offset),
    )
    work_orders = [dict(row) for row in cursor.fetchall()]

    # Get total count
    cursor.execute("SELECT COUNT(*) FROM work_orders")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'pending'")
    pending_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'completed'")
    completed_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'cancelled'")
    cancelled_count = cursor.fetchone()[0]

    conn.close()

    total_pages = (total + per_page - 1) // per_page

    # Calculate pagination range
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)

    return render_template(
        "work_orders.html",
        work_orders=work_orders,
        pending_count=pending_count,
        completed_count=completed_count,
        cancelled_count=cancelled_count,
        page=page,
        total_pages=total_pages,
        total=total,
        start_page=start_page,
        end_page=end_page,
    )


@app.route("/work-orders/<int:id>")
def work_order_detail(id):
    """Render work order detail page"""
    conn = get_db()
    cursor = conn.cursor()

    # Force a re-match on this specific order before displaying
    cursor.execute(
        "SELECT status, sku, accessory_code, match_status, location FROM work_orders WHERE id = ? AND status = 'pending'",
        (id,),
    )
    order_to_check = cursor.fetchone()

    if order_to_check:
        new_match = find_available_accessory(
            cursor, order_to_check["sku"], order_to_check["accessory_code"]
        )
        if new_match:
            if (
                order_to_check["match_status"] != "matched"
                or order_to_check["location"] != new_match["location"]
            ):
                cursor.execute(
                    "UPDATE work_orders SET match_status = 'matched', location = ? WHERE id = ?",
                    (new_match["location"], id),
                )
                conn.commit()
        else:
            if order_to_check["match_status"] != "new_one":
                cursor.execute(
                    "UPDATE work_orders SET match_status = 'new_one', location = NULL WHERE id = ?",
                    (id,),
                )
                conn.commit()

    # Get work order
    cursor.execute("SELECT * FROM work_orders WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return "Work order not found", 404
    work_order = dict(row)

    # Get accessory details if matched
    accessory_details = None
    accessory_remarks = []
    if work_order.get("match_status") == "matched":
        # Get accessory info
        cursor.execute(
            """
            SELECT a.*
            FROM accessories a
            WHERE a.sku = ? AND a.location = ?
        """,
            (work_order["sku"], work_order["location"]),
        )
        accessory = cursor.fetchone()
        if accessory:
            accessory_details = dict(accessory)

            # Get all remarks for this accessory, ordered by time desc
            cursor.execute(
                """
                SELECT id, content, created_at
                FROM remarks
                WHERE accessory_id = ?
                ORDER BY created_at DESC
            """,
                (accessory["id"],),
            )
            accessory_remarks = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return render_template(
        "work_order_detail.html",
        work_order=work_order,
        accessory_details=accessory_details,
        accessory_remarks=accessory_remarks,
    )


@app.route("/locations")
def locations_page():
    """Render locations management page"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM locations ORDER BY usage_count DESC, name ASC")
    locations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template("locations.html", locations=locations)


@app.route("/detail/<int:id>")
def detail(id):
    """Render accessory detail page"""
    conn = get_db()
    cursor = conn.cursor()

    # Get accessory
    cursor.execute("SELECT * FROM accessories WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return "Accessory not found", 404
    accessory = dict(row)

    # Get remarks
    cursor.execute(
        """
        SELECT * FROM remarks 
        WHERE accessory_id = ? 
        ORDER BY created_at DESC
    """,
        (id,),
    )
    remarks = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return render_template("detail.html", accessory=accessory, remarks=remarks)


@app.route("/sku/<sku>")
def sku_detail(sku):
    """Render SKU detail page"""
    conn = get_db()
    cursor = conn.cursor()

    # Get accessories for this SKU
    cursor.execute(
        """
        SELECT a.*, 
               (SELECT content FROM remarks 
                WHERE accessory_id = a.id 
                ORDER BY created_at DESC LIMIT 1) as latest_remark
        FROM accessories a
        WHERE a.sku = ? OR a.sku LIKE ?
        ORDER BY a.location
    """,
        (sku, f"{sku}*%"),
    )
    accessories = [dict(row) for row in cursor.fetchall()]

    # Get unique locations
    locations = list(set([a["location"] for a in accessories]))

    conn.close()

    return render_template(
        "sku_detail.html",
        base_sku=sku,
        accessories=accessories,
        locations=locations,
        total_count=len(accessories),
    )


@app.route("/update/<int:id>", methods=["POST"])
def update_accessory(id):
    """Update accessory"""
    location = request.form.get("location", "").strip()
    new_remark = request.form.get("new_remark", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    # Update location and timestamp
    cursor.execute(
        """
        UPDATE accessories 
        SET location = ?, updated_at = ?
        WHERE id = ?
    """,
        (location, datetime.now(), id),
    )

    # Add new remark if provided
    if new_remark:
        cursor.execute(
            """
            INSERT INTO remarks (accessory_id, content, created_at)
            VALUES (?, ?, ?)
        """,
            (id, new_remark, datetime.now()),
        )

    conn.commit()
    conn.close()

    return redirect(url_for("detail", id=id))


@app.route("/delete-remark/<int:remark_id>", methods=["POST"])
def delete_remark(remark_id):
    """Delete a remark"""
    conn = get_db()
    cursor = conn.cursor()

    # Get accessory_id before deleting
    cursor.execute("SELECT accessory_id FROM remarks WHERE id = ?", (remark_id,))
    result = cursor.fetchone()
    accessory_id = result["accessory_id"] if result else None

    cursor.execute("DELETE FROM remarks WHERE id = ?", (remark_id,))
    conn.commit()
    conn.close()

    if accessory_id:
        return redirect(url_for("detail", id=accessory_id))
    return redirect(url_for("index"))


@app.route("/delete/<int:id>", methods=["POST"])
def delete_accessory(id):
    """Delete accessory and redirect to index"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM accessories WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete-location/<int:location_id>", methods=["POST"])
def delete_location(location_id):
    """Delete location and redirect to locations page"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM locations WHERE id = ?", (location_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("locations_page"))


@app.route("/delete-work-order/<int:order_id>", methods=["POST"])
def delete_work_order(order_id):
    """Delete work order and redirect to work orders page"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM work_orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("work_orders_page"))


# Legacy routes for backward compatibility with tests
@app.route("/add", methods=["POST"])
def add_accessory_legacy():
    """Legacy route for adding accessories - supports form data"""
    sku = request.form.get("sku", "").strip()
    location = request.form.get("location", "").strip()
    remark = request.form.get("remark", "").strip()

    if not sku or not location:
        return jsonify(
            {"success": False, "message": "SKU and Location are required"}
        ), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Generate unique SKU
        final_sku = generate_unique_sku(cursor, sku, location)

        # Insert accessory
        cursor.execute(
            """
            INSERT INTO accessories (sku, location, updated_at)
            VALUES (?, ?, ?)
        """,
            (final_sku, location, datetime.now()),
        )

        accessory_id = cursor.lastrowid

        # Update location usage count
        cursor.execute(
            """
            UPDATE locations SET usage_count = usage_count + 1 WHERE name = ?
        """,
            (location,),
        )

        # Insert remark if provided
        if remark:
            cursor.execute(
                """
                INSERT INTO remarks (accessory_id, content, created_at)
                VALUES (?, ?, ?)
            """,
                (accessory_id, remark, datetime.now()),
            )

        # Re-match 'new_one' work orders for this SKU
        re_match_new_one_work_orders(cursor, sku)

        conn.commit()
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": f"Added successfully{' (SKU: ' + final_sku + ')' if final_sku != sku else ''}",
            }
        )
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/locations/add", methods=["POST"])
def add_location_legacy():
    """Legacy route for adding locations - supports form data"""
    name = request.form.get("name", "").strip()

    if not name:
        return jsonify({"success": False, "message": "Location name is required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO locations (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Location added successfully"})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "message": "Location already exists"}), 409


@app.route("/locations/delete/<int:location_id>", methods=["POST"])
def delete_location_legacy(location_id):
    """Legacy route for deleting locations"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM locations WHERE id = ?", (location_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("locations_page"))


@app.route("/delete_remark/<int:remark_id>", methods=["POST"])
def delete_remark_legacy(remark_id):
    """Legacy route for deleting remarks"""
    return delete_remark(remark_id)


if __name__ == "__main__":
    init_db()
    print("Accessory Management System API starting...")
    print("API URL: http://127.0.0.1:5001/api")
    app.run(debug=True, host="0.0.0.0", port=5002)
