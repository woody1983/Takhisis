#!/usr/bin/env python3
"""
Accessory Management System - Version 1
Features: Manage SKU, Location, and multiple Remarks (sorted by time, newest first)
Data Storage: SQLite Database
"""

import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os

app = Flask(__name__)
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

    conn.commit()
    conn.close()


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_locations():
    """Get all locations sorted by usage count (desc)"""
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
    """Get all unique SKUs from accessories"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT sku FROM accessories ORDER BY sku")
    skus = [row["sku"] for row in cursor.fetchall()]
    conn.close()
    return skus


def get_sku_statistics():
    """Get SKU statistics, grouping variants (*1, *2, etc.) with base SKU"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT sku FROM accessories")

    sku_counts = {}
    for row in cursor.fetchall():
        sku = row["sku"]
        # Extract base SKU (remove *1, *2, etc. suffix)
        base_sku = sku.split("*")[0] if "*" in sku else sku
        sku_counts[base_sku] = sku_counts.get(base_sku, 0) + 1

    conn.close()

    # Sort by count descending
    sorted_stats = sorted(sku_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_stats


@app.route("/")
def index():
    """Homepage - Display all accessories with pagination"""
    # Get page number from query string, default to 1
    page = request.args.get("page", 1, type=int)
    per_page = 7

    conn = get_db()
    cursor = conn.cursor()

    # Get total count for pagination
    cursor.execute("SELECT COUNT(*) as total FROM accessories")
    total_items = cursor.fetchone()["total"]
    total_pages = (total_items + per_page - 1) // per_page

    # Ensure page is within valid range
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1

    # Calculate offset
    offset = (page - 1) * per_page

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

    accessories = []
    for row in cursor.fetchall():
        accessories.append(
            {
                "id": row["id"],
                "sku": row["sku"],
                "location": row["location"],
                "updated_at": row["updated_at"],
                "latest_remark": row["latest_remark"] or "No remarks",
            }
        )

    conn.close()

    # Get locations and SKUs for the form
    locations = get_all_locations()
    skus = get_all_skus()
    sku_stats = get_sku_statistics()

    # Calculate page range for display (show up to 5 pages)
    start_page = max(1, page - 2)
    end_page = min(total_pages, start_page + 4)
    if end_page - start_page < 4 and total_pages >= 5:
        start_page = max(1, end_page - 4)

    return render_template(
        "index.html",
        accessories=accessories,
        locations=locations,
        skus=skus,
        sku_stats=sku_stats,
        page=page,
        total_pages=total_pages,
        total_items=total_items,
        start_page=start_page,
        end_page=end_page,
    )

    conn.close()

    # Get locations and SKUs for the form
    locations = get_all_locations()
    skus = get_all_skus()
    sku_stats = get_sku_statistics()

    return render_template(
        "index.html",
        accessories=accessories,
        locations=locations,
        skus=skus,
        sku_stats=sku_stats,
    )


def generate_unique_sku(cursor, sku, location):
    """Generate unique SKU, append *1, *2, etc. if duplicate"""
    # Check if SKU + Location combination exists
    cursor.execute(
        "SELECT sku FROM accessories WHERE sku = ? AND location = ?", (sku, location)
    )

    if not cursor.fetchone():
        # No duplicate, use original SKU
        return sku

    # Duplicate found, append suffix
    # Find all existing variants of this SKU at this location
    cursor.execute(
        "SELECT sku FROM accessories WHERE (sku = ? OR sku LIKE ?) AND location = ?",
        (sku, f"{sku}*%", location),
    )

    existing_skus = [row[0] for row in cursor.fetchall()]

    # Find the maximum suffix number
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

    # Generate new SKU
    if max_num == 0:
        return f"{sku}*1"
    else:
        return f"{sku}*{max_num}"


@app.route("/add", methods=["POST"])
def add_accessory():
    """Add new accessory"""
    sku = request.form.get("sku", "").strip()
    location = request.form.get("location", "").strip()
    remark = request.form.get("remark", "").strip()

    if not sku or not location:
        return jsonify({"success": False, "message": "SKU and Location are required"})

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

        # Update location usage count (use same connection)
        cursor.execute(
            "UPDATE locations SET usage_count = usage_count + 1 WHERE name = ?",
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

        conn.commit()

        # Notify user if SKU was modified
        if final_sku != sku:
            return jsonify(
                {
                    "success": True,
                    "message": f"Added successfully, SKU auto-modified to: {final_sku}",
                }
            )
        else:
            return jsonify({"success": True, "message": "Added successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to add: {str(e)}"})
    finally:
        conn.close()


@app.route("/detail/<int:id>")
def detail(id):
    """View accessory details"""
    conn = get_db()
    cursor = conn.cursor()

    # Get accessory info
    cursor.execute("SELECT * FROM accessories WHERE id = ?", (id,))
    accessory = cursor.fetchone()

    if not accessory:
        conn.close()
        return "Accessory not found", 404

    # Get all remarks (sorted by time, newest first)
    cursor.execute(
        """
        SELECT * FROM remarks 
        WHERE accessory_id = ? 
        ORDER BY created_at DESC
    """,
        (id,),
    )

    remarks = []
    for row in cursor.fetchall():
        remarks.append(
            {
                "id": row["id"],
                "content": row["content"],
                "created_at": row["created_at"],
            }
        )

    conn.close()

    return render_template("detail.html", accessory=dict(accessory), remarks=remarks)


@app.route("/update/<int:id>", methods=["POST"])
def update_accessory(id):
    """Update accessory info"""
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


@app.route("/delete/<int:id>", methods=["POST"])
def delete_accessory(id):
    """Delete accessory"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM accessories WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/delete_remark/<int:remark_id>", methods=["POST"])
def delete_remark(remark_id):
    """Delete single remark"""
    conn = get_db()
    cursor = conn.cursor()

    # Get accessory ID for redirect
    cursor.execute("SELECT accessory_id FROM remarks WHERE id = ?", (remark_id,))
    row = cursor.fetchone()
    accessory_id = row["accessory_id"] if row else None

    cursor.execute("DELETE FROM remarks WHERE id = ?", (remark_id,))
    conn.commit()
    conn.close()

    if accessory_id:
        return redirect(url_for("detail", id=accessory_id))
    return redirect(url_for("index"))


# ==================== Location Management Routes ====================


@app.route("/locations")
def locations_page():
    """Location management page"""
    locations = get_all_locations()
    return render_template("locations.html", locations=locations)


@app.route("/locations/add", methods=["POST"])
def add_location_route():
    """Add new location"""
    name = request.form.get("name", "").strip()

    if not name:
        return jsonify({"success": False, "message": "Location name is required"})

    success, message = add_location(name)
    return jsonify({"success": success, "message": message})


@app.route("/locations/delete/<int:location_id>", methods=["POST"])
def delete_location(location_id):
    """Delete location"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM locations WHERE id = ?", (location_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("locations_page"))


@app.route("/api/skus")
def api_skus():
    """API endpoint to get all SKUs"""
    skus = get_all_skus()
    return jsonify(skus)


@app.route("/api/locations")
def api_locations():
    """API endpoint to get all locations"""
    locations = get_all_locations()
    return jsonify(locations)


@app.route("/sku/<sku>")
def sku_detail(sku):
    """View all accessories for a specific SKU (including variants)"""
    conn = get_db()
    cursor = conn.cursor()

    # Get all accessories matching this base SKU (including variants like *1, *2)
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

    accessories = []
    locations = []
    for row in cursor.fetchall():
        accessories.append(
            {
                "id": row["id"],
                "sku": row["sku"],
                "location": row["location"],
                "updated_at": row["updated_at"],
                "latest_remark": row["latest_remark"] or "No remarks",
            }
        )
        locations.append(row["location"])

    conn.close()

    # Get unique locations
    unique_locations = sorted(set(locations))

    return render_template(
        "sku_detail.html",
        base_sku=sku,
        accessories=accessories,
        locations=unique_locations,
        total_count=len(accessories),
    )


if __name__ == "__main__":
    init_db()
    print("Accessory Management System starting...")
    print("Access URL: http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5001)
