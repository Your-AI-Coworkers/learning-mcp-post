from __future__ import annotations

import csv
import json
import logging
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


tool_properties_search = json.dumps([
    {
        "propertyName": "name_like",
        "propertyType": "string",
        "description": "Partial country name to match (case-insensitive).",
        "isRequired": True,
        "isArray": False,
    }
])

tool_properties_get = json.dumps([
    {
        "propertyName": "country",
        "propertyType": "string",
        "description": "Exact country name.",
        "isRequired": True,
        "isArray": False,
    }
])


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="country_count",
    description="Return the number of countries in the CSV data set.",
    tool_properties="[]",
)
def country_count_mcp(context) -> str:
    return str(len(_load_rows()))


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="search_countries",
    description="Search countries by a partial, case-insensitive name match.",
    tool_properties=tool_properties_search,
)
def search_countries_mcp(context) -> str:
    content = json.loads(context)
    name_like = content["arguments"].get("name_like", "").strip().lower()
    if not name_like:
        return json.dumps([])
    matches = [
        row for row in _load_rows()
        if name_like in row.get("Country", "").lower()
    ]
    return json.dumps(matches[:25])


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="get_country",
    description="Return a single country row by exact country name.",
    tool_properties=tool_properties_get,
)
def get_country_mcp(context) -> str:
    content = json.loads(context)
    country = content["arguments"].get("country", "").strip().lower()
    for row in _load_rows():
        if row.get("Country", "").strip().lower() == country:
            return json.dumps(row)
    return json.dumps(None)