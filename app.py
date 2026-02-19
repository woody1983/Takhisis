#!/usr/bin/env python3
"""
配件登记系统 - 第一版
功能：管理配件的SKU、库位、备注（多条，按时间降序）
数据存储：SQLite数据库
"""

import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os

app = Flask(__name__)
DB_PATH = "accessories.db"


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建配件表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accessories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            location TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建备注表
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
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    """首页 - 显示所有配件"""
    conn = get_db()
    cursor = conn.cursor()

    # 获取所有配件及其最新备注
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
                "latest_remark": row["latest_remark"] or "无备注",
            }
        )

    conn.close()
    return render_template("index.html", accessories=accessories)


def generate_unique_sku(cursor, sku, location):
    """生成唯一的SKU，如果重复则添加*1、*2等后缀"""
    # 检查是否存在相同的SKU和库位组合
    cursor.execute(
        "SELECT sku FROM accessories WHERE sku = ? AND location = ?", (sku, location)
    )

    if not cursor.fetchone():
        # 没有重复，直接使用原SKU
        return sku

    # 有重复，需要添加后缀
    # 查找该SKU在该库位已有的所有变体
    cursor.execute(
        "SELECT sku FROM accessories WHERE (sku = ? OR sku LIKE ?) AND location = ?",
        (sku, f"{sku}*%", location),
    )

    existing_skus = [row[0] for row in cursor.fetchall()]

    # 找到最大的后缀数字
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

    # 生成新的SKU
    if max_num == 0:
        return f"{sku}*1"
    else:
        return f"{sku}*{max_num}"


@app.route("/add", methods=["POST"])
def add_accessory():
    """添加新配件"""
    sku = request.form.get("sku", "").strip()
    location = request.form.get("location", "").strip()
    remark = request.form.get("remark", "").strip()

    if not sku or not location:
        return jsonify({"success": False, "message": "SKU和库位不能为空"})

    conn = get_db()
    cursor = conn.cursor()

    try:
        # 生成唯一的SKU
        final_sku = generate_unique_sku(cursor, sku, location)

        # 插入配件
        cursor.execute(
            """
            INSERT INTO accessories (sku, location, updated_at)
            VALUES (?, ?, ?)
        """,
            (final_sku, location, datetime.now()),
        )

        accessory_id = cursor.lastrowid

        # 如果有备注，插入备注
        if remark:
            cursor.execute(
                """
                INSERT INTO remarks (accessory_id, content, created_at)
                VALUES (?, ?, ?)
            """,
                (accessory_id, remark, datetime.now()),
            )

        conn.commit()

        # 如果SKU被修改了，提示用户
        if final_sku != sku:
            return jsonify(
                {"success": True, "message": f"添加成功，SKU已自动修改为：{final_sku}"}
            )
        else:
            return jsonify({"success": True, "message": "添加成功"})
    except Exception as e:
        return jsonify({"success": False, "message": f"添加失败：{str(e)}"})
    finally:
        conn.close()


@app.route("/detail/<int:id>")
def detail(id):
    """查看配件详情"""
    conn = get_db()
    cursor = conn.cursor()

    # 获取配件信息
    cursor.execute("SELECT * FROM accessories WHERE id = ?", (id,))
    accessory = cursor.fetchone()

    if not accessory:
        conn.close()
        return "配件不存在", 404

    # 获取所有备注（按时间降序）
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
    """更新配件信息"""
    location = request.form.get("location", "").strip()
    new_remark = request.form.get("new_remark", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    # 更新库位和修改时间
    cursor.execute(
        """
        UPDATE accessories 
        SET location = ?, updated_at = ?
        WHERE id = ?
    """,
        (location, datetime.now(), id),
    )

    # 如果有新备注，添加
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
    """删除配件"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM accessories WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/delete_remark/<int:remark_id>", methods=["POST"])
def delete_remark(remark_id):
    """删除单条备注"""
    conn = get_db()
    cursor = conn.cursor()

    # 获取配件ID用于重定向
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
    print("配件登记系统启动...")
    print("访问地址: http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5001)
