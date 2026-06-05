from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent
CSV_PATH = BASE / "data" / "countries.csv"
DB_PATH = BASE / "countries.sqlite"


def _build_db() -> None:
    if DB_PATH.exists() and DB_PATH.stat().st_mtime >= CSV_PATH.stat().st_mtime:
        return

    with CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file, sqlite3.connect(DB_PATH) as conn:
        reader = csv.DictReader(csv_file)
        columns = reader.fieldnames or []
        if not columns:
            raise ValueError("countries.csv has no header row")

        col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
        conn.execute("DROP TABLE IF EXISTS countries")
        conn.execute(f"CREATE TABLE countries ({col_defs})")

        placeholders = ", ".join("?" for _ in columns)
        quoted_cols = ", ".join(f'"{c}"' for c in columns)
        rows = ([row.get(c, "") for c in columns] for row in reader)
        conn.executemany(
            f"INSERT INTO countries ({quoted_cols}) VALUES ({placeholders})",
            rows,
        )
        conn.commit()


def _query(sql: str, params: tuple[str, ...] = ()) -> list[dict[str, str]]:
    _build_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def country_count() -> int:
    return int(_query("SELECT COUNT(*) AS count FROM countries")[0]["count"])


def search_countries(name_like: str) -> list[dict[str, str]]:
    return _query(
        'SELECT * FROM countries WHERE TRIM("Country") LIKE ? ORDER BY TRIM("Country") LIMIT 25',
        (f"%{name_like.strip()}%",),
    )


def get_country(country: str) -> dict[str, str] | None:
    rows = _query('SELECT * FROM countries WHERE TRIM("Country") = TRIM(?) LIMIT 1', (country,))
    return rows[0] if rows else None


def register(mcp) -> None:
    _build_db()

    @mcp.tool()
    def country_count_tool() -> int:
        """Return the number of rows in the countries SQLite database."""
        return country_count()

    @mcp.tool()
    def search_countries_tool(name_like: str) -> list[dict[str, str]]:
        """Search countries by partial name match."""
        return search_countries(name_like)

    @mcp.tool()
    def get_country_tool(country: str) -> dict[str, str] | None:
        """Return a single country row by exact country name."""
        return get_country(country)
