# MCP Tutorial Series
---

## Tutorial # 01 : **Hello World**

> **Purpose:** Steps to set up, run, and test the MCP local server with OpenAI Codex

> **Date:** 2026-06-02

> **Status:** Final

> **Version:** v2

---

## Project Layout

```
learning-mcp/
└── 01-helloworld/
    ├── .python-version
    ├── README.md
    ├── main.py
    ├── pyproject.toml
    ├── server.py
    ├── uv.lock
    └── .venv/
```

---

## Step 0 — Verify uv is Installed

```bash
uv --version
```

Expected: `uv 0.x.x` (any version). If the command is not found, install uv:

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, restart your terminal and re-run `uv --version` to confirm.

---

## Step 1 — Bootstrap the Project

```bash
# In VS Code terminal, navigate to the project folder:
cd learning-mcp/01-helloworld

uv init --no-readme        # skip if pyproject.toml already present
uv venv                    # creates .venv/
uv sync                    # installs current project dependencies into .venv
```

Select the `.venv` interpreter in VS Code:
`Ctrl+Shift+P` → `Python: Select Interpreter` → choose `.venv`

---

## Step 2 — Let Codex Create the MCP Server

Ask Codex to write `server.py` and connect the generated `main.py` entry point to it.

Example prompt:

```text
Create a simple MCP server in server.py using FastMCP.

Requirements:
- Use Streamable HTTP on 127.0.0.1:8000 with path /mcp.
- Configure host, port, and streamable_http_path on the FastMCP constructor.
- Start the server with mcp.run(transport="streamable-http"); do not pass host, port, or path to run().
- Register one tool named hello_from_mcp that returns a short greeting.
- Keep the FastMCP server object reusable as mcp.
- Update main.py so running main.py starts the same server from server.py.
- Make sure pyproject.toml includes the mcp[cli] dependency.
```

Expected result:

```text
server.py defines the MCP server and tool.
main.py imports the server object from server.py and runs it.
pyproject.toml includes mcp[cli].
```

After Codex updates the files, run:

```bash
uv sync
```

---

## Step 3 — Run the Server

```bash
uv run python server.py
```

Expected output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Leave this terminal open. The server blocks — it is now listening.

---

## Step 4 — Inspect via MCP Inspector

MCP Inspector is a browser-based GUI for testing MCP servers directly — independent of any AI client.

No install required. Run from any terminal:

```bash
npx @modelcontextprotocol/inspector --verbose
```

Expected output:
```
MCP Inspector running at http://localhost:6274
```

Open `http://localhost:6274` in your browser.

In the Inspector UI:
1. Set transport to `Streamable HTTP`
2. Enter URL: `http://127.0.0.1:8000/mcp`
3. Click **Connect**
4. Navigate to **Tools** tab — `hello_from_mcp` should appear
5. Click the tool → click **Run** — verify the greeting response

Use MCP Inspector to validate tool metadata (name, description, input schema) independently of Codex. This is the fastest way to debug tool registration issues.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv not installed | Follow Step 0 install instructions |
| `Connection refused` on port 8000 | server.py not running | Run `uv run python server.py` first |
| `ModuleNotFoundError: mcp` | venv not activated or sync not run | `uv sync` then retry |
| Tool returns error | MCP version mismatch | Confirm `mcp>=1.9.0` via `uv pip show mcp` |
| Inspector can't connect | Wrong transport selected | Set transport to `Streamable HTTP`, not SSE |
