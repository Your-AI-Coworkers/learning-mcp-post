# Part 3: Test MCP with MCP Inspector and Claude Chrome Extension

Purpose: Provide a paste-ready prompt for Claude's Chrome extension to validate the local hello-world MCP server through MCP Inspector.

Date: 2026-06-01

Status: Draft v1

---

## Copy/Paste Prompt for Claude Chrome Extension

Paste the following prompt into Claude's Chrome extension.

```text
You are helping me validate a local hello-world MCP server by using MCP Inspector in Chrome.

Your job:
- Use the browser UI only.
- Do not edit files.
- Do not run terminal commands.
- Do not assume success.
- Validate the MCP server through MCP Inspector and report the evidence.

Context:
- The MCP server should already be running locally.
- Server URL: http://127.0.0.1:8000/mcp
- Transport: Streamable HTTP
- MCP Inspector should already be running locally.
- Inspector URL is usually: http://localhost:6274
- The expected MCP tool is: hello_from_mcp
- The expected tool response is: Hello from the local MCP server.

Steps:
1. Open http://localhost:6274 in Chrome.
2. If MCP Inspector opens at a different local URL, use the Inspector page that is available.
3. In MCP Inspector, set the transport to Streamable HTTP.
4. Enter the server URL: http://127.0.0.1:8000/mcp
5. Click Connect.
6. Confirm whether the connection succeeds.
7. Open the Tools section or Tools tab.
8. Confirm whether the tool hello_from_mcp is listed.
9. Run hello_from_mcp.
10. Capture the returned response text.

Success criteria:
- MCP Inspector connects to http://127.0.0.1:8000/mcp.
- The tool hello_from_mcp appears in the Tools list.
- Running hello_from_mcp returns: Hello from the local MCP server.

If anything fails:
- Say exactly which step failed.
- Quote the visible error message if there is one.
- Do not invent missing output.
- Suggest the most likely fix based on the visible evidence.

Final response format:

MCP validation result: PASS or FAIL

Evidence:
- Inspector opened: yes/no, with URL
- Connected to server: yes/no
- Transport used: Streamable HTTP
- Server URL used: http://127.0.0.1:8000/mcp
- Tool found: yes/no
- Tool response: exact response text, or none

Notes:
- If you cannot access localhost from the Chrome extension, say that clearly.
- If the server is not running, the likely symptom is connection refused or failed connection.
- If the wrong transport is selected, switch to Streamable HTTP and retry once.
```

---

## Preconditions Before Using the Prompt

Before pasting the prompt into Claude's Chrome extension, complete Part 2 through the point where both of these are running:

1. MCP server:

```powershell
uv run python server.py
```

Expected server endpoint:

```text
http://127.0.0.1:8000/mcp
```

2. MCP Inspector:

```powershell
npx @modelcontextprotocol/inspector
```

Expected Inspector endpoint:

```text
http://localhost:6274
```

Keep both terminals open while Claude performs the browser validation.

---

## Expected Claude Validation Output

Claude should report something like:

```text
MCP validation result: PASS

Evidence:
- Inspector opened: yes, with URL http://localhost:6274
- Connected to server: yes
- Transport used: Streamable HTTP
- Server URL used: http://127.0.0.1:8000/mcp
- Tool found: yes
- Tool response: Hello from the local MCP server.
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Claude cannot open `localhost` | Chrome extension cannot access the local page | Open MCP Inspector manually in Chrome, then ask Claude to use the current page |
| Inspector shows connection refused | MCP server is not running | Start the server with `uv run python server.py` |
| Inspector connects but no tools appear | Wrong server URL or server did not register the tool | Use `http://127.0.0.1:8000/mcp` and verify `server.py` defines `hello_from_mcp` |
| Inspector fails with transport error | Wrong transport selected | Select `Streamable HTTP` and retry |
| Tool response is different | Server implementation differs from the spec | Compare `hello_from_mcp` in `server.py` with the expected response |
