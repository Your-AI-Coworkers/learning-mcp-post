from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from tools_countries import country_count, get_country, search_countries, register

BASE = Path(__file__).parent
CSV_PATH = BASE / "countries.csv"
DB_PATH = BASE / "countries.sqlite"

mcp = FastMCP("countries-sqlite-api", host="127.0.0.1", port=8001, streamable_http_path="/mcp")


def _build_db() -> None:
    if DB_PATH.exists() and DB_PATH.stat().st_mtime >= CSV_PATH.stat().st_mtime:
        return

    with CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file, sqlite3.connect(DB_PATH) as conn:
        reader = csv.DictReader(csv_file)
        columns = reader.fieldnames or []
        if not columns:
            raise ValueError("countries.csv has no header row")

        col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
        conn.execute('DROP TABLE IF EXISTS countries')
        conn.execute(f'CREATE TABLE countries ({col_defs})')

        placeholders = ", ".join("?" for _ in columns)
        quoted_cols = ", ".join(f'"{c}"' for c in columns)
        rows = ([row.get(c, "") for c in columns] for row in reader)
        conn.executemany(
            f'INSERT INTO countries ({quoted_cols}) VALUES ({placeholders})',
            rows,
        )
        conn.commit()


def _query(sql: str, params: tuple[str, ...] = ()) -> list[dict[str, str]]:
    _build_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def run() -> None:
    _build_db()

    register(mcp)
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    run()
