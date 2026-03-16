#!/usr/bin/env python3
"""Inspect database schema for EHRSQL tasks."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-id", required=True, choices=["mimic_iii", "eicu"])
    parser.add_argument("--table", help="Specific table name to inspect")
    args = parser.parse_args()

    db_dir = Path("/data/ehrsql") / args.db_id
    db_file = db_dir / f"{args.db_id}.sqlite"

    if not db_file.exists():
        print(f"Error: Database file not found: {db_file}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    try:
        if args.table:
            # Show schema for specific table
            cursor.execute(f"PRAGMA table_info({args.table})")
            columns = cursor.fetchall()
            print(f"Table: {args.table}")
            print(f"{'Column':<30} {'Type':<20}")
            print("-" * 50)
            for col_id, col_name, col_type, notnull, dflt, pk in columns:
                print(f"{col_name:<30} {col_type:<20}")

            # Show sample row
            cursor.execute(f"SELECT * FROM {args.table} LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                print(f"\nSample row: {sample}")
        else:
            # List all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Database: {args.db_id}")
            print(f"Tables ({len(tables)}):")
            for table in sorted(tables):
                print(f"  - {table}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
