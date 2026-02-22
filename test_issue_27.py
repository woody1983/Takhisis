import pytest
import sqlite3
import os
from app import app, find_available_accessory

@pytest.fixture
def db():
    """Create a temporary in-memory database with the required schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE accessories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            location TEXT NOT NULL,
            updated_at DATETIME
        )
    """)
    cursor.execute("""
        CREATE TABLE remarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            accessory_id INTEGER,
            content TEXT,
            created_at DATETIME,
            FOREIGN KEY (accessory_id) REFERENCES accessories (id)
        )
    """)
    return conn

def add_accessory(cursor, sku, location, remark=None):
    cursor.execute(
        "INSERT INTO accessories (sku, location, updated_at) VALUES (?, ?, '2026-02-21 12:00:00')",
        (sku, location)
    )
    acc_id = cursor.lastrowid
    if remark:
        cursor.execute(
            "INSERT INTO remarks (accessory_id, content, created_at) VALUES (?, ?, '2026-02-21 12:00:01')",
            (acc_id, remark)
        )
    return acc_id

class TestRemarkExtraction:
    def test_basic_match(self, db):
        """Test that accessory is found when no disqualifying remarks exist."""
        cursor = db.cursor()
        add_accessory(cursor, "SKU123", "LOC1")
        
        result = find_available_accessory(cursor, "SKU123", "PART-A")
        assert result is not None
        assert result["location"] == "LOC1"

    def test_legacy_remove_pattern(self, db):
        """Test existing 'remove part' pattern."""
        cursor = db.cursor()
        add_accessory(cursor, "SKU123", "LOC1", "remove PART-A")
        
        result = find_available_accessory(cursor, "SKU123", "PART-A")
        assert result is None

    def test_missing_prefix_pattern(self, db):
        """Test 'Missing PART-A' pattern."""
        cursor = db.cursor()
        add_accessory(cursor, "SKU123", "LOC1", "Missing PART-A")
        
        result = find_available_accessory(cursor, "SKU123", "PART-A")
        assert result is None

    def test_missing_suffix_pattern(self, db):
        """Test 'PART-A is missing' pattern."""
        cursor = db.cursor()
        add_accessory(cursor, "SKU123", "LOC1", "PART-A is missing")
        
        result = find_available_accessory(cursor, "SKU123", "PART-A")
        assert result is None

    def test_long_sentence_pattern(self, db):
        """Test complex sentence: 'We found that PART-A is missing from the package.'"""
        cursor = db.cursor()
        add_accessory(cursor, "SKU123", "LOC1", "We found that PART-A is missing from the package.")
        
        result = find_available_accessory(cursor, "SKU123", "PART-A")
        assert result is None

    def test_case_insensitivity(self, db):
        """Test that matching is case-insensitive."""
        cursor = db.cursor()
        add_accessory(cursor, "SKU123", "LOC1", "missing part-a")
        
        result = find_available_accessory(cursor, "SKU123", "PART-A")
        assert result is None

    def test_partial_match_protection(self, db):
        """Ensure it doesn't accidentally block 'PART-A' if remark says 'PART-AB is missing'."""
        cursor = db.cursor()
        add_accessory(cursor, "SKU123", "LOC1", "Missing PART-AB")
        
        result = find_available_accessory(cursor, "SKU123", "PART-A")
        assert result is not None  # Should still match because PART-A is not PART-AB

    def test_multiple_remarks(self, db):
        """Test that any record in history can block the match."""
        cursor = db.cursor()
        acc_id = add_accessory(cursor, "SKU123", "LOC1", "Looks good")
        cursor.execute(
            "INSERT INTO remarks (accessory_id, content, created_at) VALUES (?, ?, '2026-02-21 13:00:00')",
            (acc_id, "Wait, PART-A is missing")
        )
        
        result = find_available_accessory(cursor, "SKU123", "PART-A")
        assert result is None
