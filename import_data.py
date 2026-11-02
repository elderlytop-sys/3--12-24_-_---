#!/usr/bin/env python3
"""Импорт CSV-файлов в SQLite. Запуск из корня репозитория: python import_data.py"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDIVIDUAL = ROOT / "02_individual"
DB_PATH = INDIVIDUAL / "repair_service.db"
CSV_DIR = INDIVIDUAL / "csv"
SQL_DIR = INDIVIDUAL / "sql"

ORDER = [
    ("customers", "customers.csv"),
    ("device_types", "device_types.csv"),
    ("employees", "employees.csv"),
    ("repair_statuses", "repair_statuses.csv"),
    ("services", "services.csv"),
    ("devices", "devices.csv"),
    ("repair_orders", "data.csv"),
    ("order_services", "order_services.csv"),
]

def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript((SQL_DIR / "01_create_tables.sql").read_text(encoding="utf-8"))
        for table, filename in ORDER:
            with (CSV_DIR / filename).open("r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames
                placeholders = ",".join("?" for _ in columns)
                sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                rows = []
                for row in reader:
                    rows.append([None if v == "" else v for v in row.values()])
                conn.executemany(sql, rows)
                print(f"{table}: imported {len(rows)} rows")
        conn.executescript((SQL_DIR / "02_indexes.sql").read_text(encoding="utf-8"))
        conn.commit()
        print(f"Database created: {DB_PATH}")
        print("Tables:", ", ".join(r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )))
    finally:
        conn.close()

if __name__ == "__main__":
    main()
