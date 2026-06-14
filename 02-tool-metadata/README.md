# MCP Tutorial — **Tool Metadata**
*The Contract Between LLM and Execution*

---

> **Purpose:** Learn how tool metadata (name, description, inputSchema, outputSchema) controls LLM tool selection and argument generation — without changing implementation code.

> **Date:** 2026-06-06

> **Status:** Draft

> **Version:** v1

> **Prerequisite:** [Tutorial 01 — Hello World](/01-helloworld/README.md)

---

## Parts

> [Part 1: Concepts and Theory](README-part1-concepts.md) — How an LLM "sees" tools, the 5-beat lifecycle, why labels matter at scale.

> [Part 2: Lab — Bad Tools vs Good Tools](README-part2-lab.md) — Four lessons (Name, Description, Input Schema, Output Schema) transforming "Lazy Friday" registration into "Good Monday" metadata.

> Part 3: Deployment and Client Access *(coming soon)*

---

## Project Layout

```
learning-mcp/
└── 02-tool-metadata/
    ├── .python-version
    ├── README.md                        ← you are here
    ├── README-part1-concepts.md         ← theory
    ├── README-part2-lab.md              ← lab
    ├── main.py                          ← entry point
    ├── countries_server.py              ← FastMCP server
    ├── countries_tool_registration.py   ← tool metadata (what we change)
    ├── countries_tools.py               ← data-access layer (what we don't)
    ├── countries_db_api.py              ← SQLite access
    ├── countries_sqlite_api_test.py     ← tests
    ├── countries.sqlite                 ← built database
    ├── data/
    │   └── countries.csv                ← source dataset (227 countries, 20 columns)
    ├── docs/
    │   └── 02_journal.md
    ├── pyproject.toml
    ├── uv.lock
    └── .venv/
```

---

## Step 0 — Prerequisites

Confirm uv and the Tutorial 01 setup are working:

```bash
uv --version
```

---

## Step 1 — Bootstrap the Project

```bash
cd learning-mcp/02-tool-metadata

uv venv
uv sync
```

Select the `.venv` interpreter in VS Code:
`Ctrl+Shift+P` → `Python: Select Interpreter` → choose `.venv`

---

## Step 2 — Build the SQLite Database

The CSV in `data/countries.csv` needs to be loaded into `countries.sqlite`. If the database file already exists, skip this step.

```bash
uv run python countries_db_api.py
```

---

## Step 3 — Run the Server

```bash
uv run python main.py
```

Expected output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## Step 4 — Inspect via MCP Inspector

```bash
npx @modelcontextprotocol/inspector --verbose
```

In the Inspector UI:
1. Set transport to `Streamable HTTP`
2. Enter URL: `http://127.0.0.1:8000/mcp`
3. Click **Connect**
4. Navigate to **Tools** tab — `count_countries`, `search_countries_by_name`, and `lookup_country` should appear
5. Inspect each tool's metadata: name, description, inputSchema, outputSchema
6. Run each tool and compare the output against the schema

---

## Key Concept

**The implementation doesn't change. The metadata does. And the behaviour changes completely.**

The entire lab modifies only `countries_tool_registration.py` — the four labels (name, description, inputSchema, outputSchema). Every line of SQL, every query function, every return statement in `countries_tools.py` stays untouched.

| Label | Controls | Bad version | Good version |
|---|---|---|---|
| Name | Which tool the model reaches for | `get_country_tool` | `lookup_country` |
| Description | Whether and when the model uses the tool | "Search countries by partial name match." | Multi-sentence: what, when, what-comes-back, tool choreography |
| Input Schema | What arguments the model is allowed to pass | Bare `"type": "string"` | `Literal` enums, descriptive parameter names, defaults |
| Output Schema | What shape the model can count on getting back | `additionalProperties: {"type": "string"}` | `TypedDict` with all 20 field names |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv not installed | See Tutorial 01, Step 0 |
| `Connection refused` on port 8000 | Server not running | Run `uv run python main.py` first |
| `ModuleNotFoundError: mcp` | venv not synced | `uv sync` then retry |
| No tools in Inspector | Registration not wired | Confirm `countries_server.py` calls `register(mcp)` |
| `countries.sqlite` not found | Database not built | Run `uv run python countries_db_api.py` |

---

> [< Previous: Tutorial 01 — Hello World](/01-helloworld/README.md)

