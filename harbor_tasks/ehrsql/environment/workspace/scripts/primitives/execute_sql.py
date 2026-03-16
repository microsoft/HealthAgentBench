#!/usr/bin/env python3
"""Execute SQL queries against EHRSQL databases."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-id", required=True, choices=["mimic_iii", "eicu"])
    parser.add_argument("--query", required=True, help="SQL query to execute")
    parser.add_argument("--timeout", type=int, default=30, help="Query timeout in seconds")
    args = parser.parse_args()

    db_dir = Path("/data/ehrsql") / args.db_id
    db_file = db_dir / f"{args.db_id}.sqlite"

    if not db_file.exists():
        print(f"Error: Database file not found: {db_file}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_file))
    conn.timeout = args.timeout

    try:
        cursor = conn.cursor()
        cursor.execute(args.query)
        rows = cursor.fetchall()

        # Get column names
        col_names = [desc[0] for desc in cursor.description] if cursor.description else []

        # Format results as list of dicts
        results = [dict(zip(col_names, row)) for row in rows]

        # Output JSON
        output = {
            "status": "success",
            "row_count": len(results),
            "columns": col_names,
            "rows": results,
        }
        print(json.dumps(output, indent=2))
    except sqlite3.Error as e:
        output = {
            "status": "error",
            "error": str(e),
        }
        print(json.dumps(output, indent=2), file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
