# MCP Tutorial - Azure Functions MCP with Auth
*This lesson hosts a small Model Context Protocol server inside Azure Functions with **Authorization** enabled.*

---



## Enabling Auth on the MCP Endpoint

### Background

The MCP webhook endpoint (`/runtime/webhooks/mcp`) has two independent auth layers:

| Layer | Controlled by | Tutorial setting |
|---|---|---|
| Azure App Service (EasyAuth) | Azure Portal → Authentication | Allow unauthenticated access |
| MCP system-key auth | `host.json` → `webhookAuthorizationLevel` | Anonymous → **System** |

Tutorial 03 left EasyAuth set to **Allow unauthenticated access** and `webhookAuthorizationLevel` set to **Anonymous** — the MCP endpoint required no credentials.

This section switches `webhookAuthorizationLevel` to **System**, which requires callers to supply the `mcp_extension` system key on every request. Note: `Function` is not a valid value for this setting — the MCP extension only recognises `Anonymous` and `System`.

EasyAuth is not changed. The two layers are independent.

---

### Step 1 — Edit `host.json`

Change `webhookAuthorizationLevel` from `"Anonymous"` to `"System"`:

```json
{
  "version": "2.0",
  "extensions": {
    "mcp": {
      "instructions": "Use these tools to explore a small countries data set.",
      "serverName": "countries-azure-functions-mcp",
      "serverVersion": "1.0.0",
      "system": {
        "webhookAuthorizationLevel": "System"
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.32.0, 5.0.0)"
  }
}
```

---

### Step 2 — Redeploy

**Prerequisite — if `.azure/` is missing (new machine or after git checkout):**

The `.azure/` folder is intentionally excluded from git — azd writes `*` to `.azure/.gitignore` on first init, so the environment record is machine-local and is not restored by `git pull` or `git checkout`. Recreate it before deploying:

```powershell
azd env new 03-azure-functions-mcp-dev
azd env set AZURE_SUBSCRIPTION_ID 16adb443-eda1-4df5-aa83-afff2fb957aa
azd env set AZURE_LOCATION eastus
azd env refresh
```

`azd env refresh` pulls the existing deployment state from Azure and re-hydrates the local `.env` file. Skip this block if `.azure/` is already present from the Tutorial 03 session.

```bash
azd deploy
```

Wait for deploy to complete (~60–90 seconds). Provision (`azd up`) is not required — only the function code and configuration change.

---

### Step 3 — Retrieve the `mcp_extension` System Key

The MCP extension enforces the system key named `mcp_extension` — not a function key. Function keys will not satisfy this auth requirement.

**Azure Portal:**
`func-api-bghqx56kinrlu` → **App Keys** → **System keys** → copy `mcp_extension`

**Azure CLI:**
```bash
az functionapp keys list `
  --name func-api-bghqx56kinrlu `
  --resource-group rg-03-azure-functions-mcp-dev `
  --query "systemKeys.mcp_extension" `
  --output tsv
```

---

### Step 4 — Validate (PowerShell)

**With key — expect HTTP 200 and valid JSON-RPC response:**
```powershell
$body = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

Invoke-RestMethod `
  -Method POST `
  -Uri "https://func-api-bghqx56kinrlu.azurewebsites.net/runtime/webhooks/mcp?code=<MCP_EXTENSION_SYSTEM_KEY>" `
  -ContentType "application/json" `
  -Headers @{ "Accept" = "application/json, text/event-stream" } `
  -Body $body
```

Expected: `serverInfo.name = countries-azure-functions-mcp`

**Without key — expect HTTP 401:**
```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri "https://func-api-bghqx56kinrlu.azurewebsites.net/runtime/webhooks/mcp" `
  -ContentType "application/json" `
  -Headers @{ "Accept" = "application/json, text/event-stream" } `
  -Body $body
```

---

### Step 5 — MCP Inspector (optional)

MCP Inspector v0.22.0 → Streamable HTTP → Via Proxy

URL: `https://func-api-bghqx56kinrlu.azurewebsites.net/runtime/webhooks/mcp?code=<MCP_EXTENSION_SYSTEM_KEY>`

Connect → Tools tab should show `country_count`, `search_countries`, `get_country`.

Note: append `?code=<key>` directly to the URL — Inspector has no dedicated key field for webhook auth.

---


**TODO**

### Production Path — Entra ID (Bearer Token Auth)

System-key auth is sufficient for tutorial and internal tooling. For production exposure — where the MCP server is a shared service called by multiple clients or agents — replace function-key auth with Entra ID:

1. Re-enable EasyAuth via Azure Portal (`func-api-bghqx56kinrlu` → Settings → Authentication → Add provider → Microsoft)
2. Set **Restrict access** to **Require authentication**
3. Set **Unauthenticated requests** to **HTTP 401**
4. Callers acquire a Bearer token from Entra (`client_credentials` flow for agents, `authorization_code` for user-facing clients) and pass it as `Authorization: Bearer <token>`
5. Revert `webhookAuthorizationLevel` to `"Anonymous"` — EasyAuth becomes the sole gate; function keys are not issued to external callers

[ASSUMPTION] Entra app registration (`entraApp` Bicep module) is already present in `infra/` from the Tutorial 03 deploy — re-enabling EasyAuth binds to that registration without reprovisioning.

> **Note:** Subsequent `azd provision` runs will re-enable EasyAuth (the `entraApp` Bicep module does not have an `authEnabled` gate). If you run `azd provision` after setting function-key auth, repeat the EasyAuth Portal fix from Tutorial 03 Block 5.

---

## Next

- Client test
    - Claude Cowork
    - Copilot