# Part 2: Run and Verify the MCP Server

Purpose: Run the local hello-world MCP server.

Date: 2026-06-01

Status: Draft v1

---

## Scope

This is Part 2 of the hello-world MCP workflow.

Use this spec after Part 1 has already created the project files:

```text
01-helloworld/
├── .python-version
├── main.py
├── pyproject.toml
├── server.py
├── uv.lock
└── .venv/
```

This spec does not create or rewrite the MCP server. It only runs and verifies the server.

---

## Expected Server Contract

Before running the server, confirm the project follows this contract:

- `pyproject.toml` includes `mcp[cli]>=1.9.0`.
- `server.py` defines a reusable `mcp` object from `FastMCP`.
- `server.py` configures Streamable HTTP on `127.0.0.1:8000` with path `/mcp`.
- `server.py` registers a tool named `hello_from_mcp`.
- `main.py` starts the same server defined in `server.py`.

Important FastMCP API detail:

- Put `host`, `port`, and `streamable_http_path` on the `FastMCP(...)` constructor.
- Start the server with `mcp.run(transport="streamable-http")`.
- Do not pass `host`, `port`, or `streamable_http_path` to `mcp.run(...)`.

---

## Step 0 - Open the Project Folder

In PowerShell:

```powershell
cd D:\projects\learning-mcp\01-helloworld
```

---

## Step 1 - Sync Dependencies

```powershell
uv sync
```

Expected:

```text
Resolved packages...
Checked packages...
```

If dependencies were already installed, `uv sync` may complete almost immediately.

---

## Step 2 - Sanity Check the Python Files

```powershell
uv run python -m py_compile server.py main.py
```

Expected: no output and exit code `0`.

Optional runtime check:

```powershell
uv run python -c "import server; print(server.mcp.settings.host, server.mcp.settings.port, server.mcp.settings.streamable_http_path)"
```

Expected:

```text
127.0.0.1 8000 /mcp
```

---

## Step 3 - Run the MCP Server

Use one terminal for the server:

```powershell
uv run python server.py
```

Expected output includes:

```text
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Leave this terminal open. The server blocks while it listens for MCP clients.

---

```text
Ctrl+C
```

---

