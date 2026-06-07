from __future__ import annotations

import csv
from pathlib import Path

import azure.functions as func

app = func.FunctionApp()

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "data" / "countries.csv"


def _load_rows() -> list[dict[str, str]]:
    with CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
        ]


def _country_rows() -> list[dict[str, str]]:
    return _load_rows()


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="country_count",
    description="Return the number of countries in the CSV data set.",
    toolProperties="[]",
)
def country_count_mcp(context) -> int:
    return len(_country_rows())


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="search_countries",
    description="Search countries by a partial, case-insensitive name match.",
    toolProperties='[{"propertyName":"name_like","propertyType":"string","description":"Partial country name to match.","isRequired":true,"isArray":false}]',
)
def search_countries_mcp(context) -> list[dict[str, str]]:
    name_like = str(context.trigger_metadata.get("mcptoolargs", {}).get("name_like", "")).strip().lower()
    if not name_like:
        return []

    matches: list[dict[str, str]] = []
    for row in _country_rows():
        country = row.get("Country", "")
        if name_like in country.lower():
            matches.append(row)
    return matches[:25]


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="get_country",
    description="Return a single country row by exact country name.",
    toolProperties='[{"propertyName":"country","propertyType":"string","description":"Exact country name.","isRequired":true,"isArray":false}]',
)
def get_country_mcp(context) -> dict[str, str] | None:
    country = str(context.trigger_metadata.get("mcptoolargs", {}).get("country", "")).strip().lower()
    if not country:
        return None

    for row in _country_rows():
        if row.get("Country", "").strip().lower() == country:
            return row
    return None
