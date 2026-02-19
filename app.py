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

    conn.commit()
    conn.close()


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    """Homepage - Display all accessories"""
    conn = get_db()
    cursor = conn.cursor()

    # Get all accessories and their latest remarks
    cursor.execute("""
        SELECT a.*, 
               (SELECT content FROM remarks 
                WHERE accessory_id = a.id 
                ORDER BY created_at DESC LIMIT 1) as latest_remark
        FROM accessories a
        ORDER BY a.updated_at DESC
    """)

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
    return render_template("index.html", accessories=accessories)


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


if __name__ == "__main__":
    init_db()
    print("Accessory Management System starting...")
    print("Access URL: http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5001)
