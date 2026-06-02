# Part 2: Run and Verify the MCP Server

Purpose: Run the local hello-world MCP server and verify it with MCP Inspector.

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

## Step 4 - Run MCP Inspector

Open a second terminal and run:

```powershell
npx @modelcontextprotocol/inspector
```

Expected output includes a local Inspector URL, commonly:

```text
MCP Inspector running at http://localhost:6274
```

Open that URL in your browser.

---

## Step 5 - Connect Inspector to the Server

In MCP Inspector:

1. Set transport to `Streamable HTTP`.
2. Enter server URL: `http://127.0.0.1:8000/mcp`.
3. Click `Connect`.
4. Open the `Tools` tab.
5. Confirm `hello_from_mcp` appears.
6. Run `hello_from_mcp`.

Expected tool response:

```text
Hello from the local MCP server.
```

If the tool appears and returns the greeting, the local MCP server is working.

---

## Step 6 - Stop the Server

When finished, return to the server terminal and press:

```text
Ctrl+C
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed or not on PATH | Install uv, restart the terminal, then run `uv --version` |
| `ModuleNotFoundError: mcp` | Dependencies are not synced | Run `uv sync` |
| `TypeError` mentioning `FastMCP.run()` | Host, port, or path were passed to `mcp.run(...)` | Move HTTP config to `FastMCP(...)` and call `mcp.run(transport="streamable-http")` |
| `Connection refused` in Inspector | Server is not running | Start the server with `uv run python server.py` |
| Inspector cannot connect | Wrong transport or URL | Use `Streamable HTTP` and `http://127.0.0.1:8000/mcp` |
| Port `8000` is already in use | Another process is using the port | Stop the other process or update the server port consistently |
