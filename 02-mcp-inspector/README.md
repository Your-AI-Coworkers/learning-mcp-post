
# MCP Inspector How To

Bare minimum setup for running the local MCP server and testing it with MCP Inspector.


## Steps to Hello World MCP

### Required Environment Setup

- Python **FastMCP** based MCP Server.
- **uv** will be used for scaffolding.
- Node.js based **MCP Inspector** will be used for client side testing.


### Start Environment Setup

- Verify uv

```powershell
uv --version


uv init --no-readme
uv add "mcp[cli]"
uv sync

```


### Create MCP Server

- Create server.py
    - Basic one tool MCP server.
    


### Run the Server

- In a terminal 

```powershell
uv run python server.py
```

- Open another terminal

```powershell
npx @modelcontextprotocol/inspector --verbose
```


### Test server 

- In a browser open MCP Inspector
	- Set transport to `Streamable HTTP`.
	- Enter URL: `http://127.0.0.1:8000/mcp`.
	- Click `Connect`.
	- Open `Tools`.
	- Run `hello_from_mcp` and verify the greeting response.