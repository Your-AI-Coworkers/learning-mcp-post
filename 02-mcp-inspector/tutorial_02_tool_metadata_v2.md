# MCP Tutorial Series
---

## Tutorial # 02 : **Tool Metadata — The Contract Between LLM and Execution**

> **Purpose:** Teach why a tool's `name`, `description`, `inputSchema`, and `outputSchema` are the control surface for LLM tool integration — and how to inspect each field with MCP Inspector, against real data.

> **Audience:** Enterprise architects evaluating MCP for production integration.

> **Date:** 2026-06-03

> **Status:** Draft

> **Version:** v2

> **Prerequisite:** Tutorial 01 (Hello World) — a running FastMCP server over Streamable HTTP, inspected once.

---

## Why This Tutorial Exists

Tutorial 01 proved a tool can be reached. It answered *can the LLM see the server*. It did not answer the question that decides whether MCP survives contact with production:

> **When the LLM has a dozen tools and an ambiguous user request, does it pick the right tool, build a valid call, and get back something the rest of the system can trust?**

That outcome is not decided by your function bodies. It is decided by four pieces of metadata attached to every tool:

- **`name`** — the tool's identifier
- **`description`** — natural-language statement of what it does and when to use it
- **`inputSchema`** — the typed contract for arguments the caller must supply
- **`outputSchema`** — the typed contract for what the tool returns

For an enterprise architect, the reframe is this: **tool metadata is a control plane, not documentation.** It is how you steer model behavior without touching weights, without fine-tuning, and without trusting the model to guess. Treat it casually and you get the failure modes that make leadership distrust the whole integration — wrong tool fired, garbage arguments, results no downstream service can parse.

This tutorial builds three lessons across four tools (plus the Tutorial 01 baseline). The schema lessons run against a **real public dataset** so the contracts constrain actual rows, not hand-waved stubs.

---

## Part 1 — The Mechanism: How an LLM Actually "Sees" Your Tools

Most MCP confusion comes from a wrong mental model. Engineers picture the LLM *calling* a function the way code calls a method. That is not what happens. Understanding the real sequence is the foundation for every metadata decision that follows.

### The actual lifecycle

1. **Discovery.** The MCP client connects to the server and issues `tools/list`. The server returns, for every tool, its `name`, `description`, `inputSchema`, and (when defined) `outputSchema`.
2. **Injection.** The client serializes those tool definitions into the model's context window — as **text tokens**, alongside the system prompt and the user message. The model does not "have" your tools; it has a *textual description* of them sitting in its prompt.
3. **Selection and argument construction.** When the user asks something, the model runs next-token prediction conditioned on the whole context. It *emits* a structured request: a tool name plus a JSON arguments object. The model executes nothing. It is pattern-matching the user's intent against the descriptions and schemas it can see.
4. **Validation and execution.** The client validates the emitted arguments against `inputSchema`. Valid → it calls your function. Invalid → it can reject before any code runs.
5. **Return.** Your function's result — shaped by `outputSchema` — goes *back into the context window* as more tokens, for the model to read, cite, or chain into the next step.

### Why this makes metadata a control point

Every metadata field maps to one decision in that loop:

| Field | Controls | Failure when weak |
|---|---|---|
| `name` | Which tool the model reaches for first | Confuses near-identical names → wrong tool selected |
| `description` | *Whether and when* the model uses the tool at all | Vague text → tool under-used (model misses applicability) or mis-used (applied to wrong intent) |
| `inputSchema` | What arguments the model is *permitted* to construct | Loose schema → model invents argument shapes → runtime errors or silent wrong behavior |
| `outputSchema` | What the model and downstream code can rely on receiving | No contract → results are an opaque string → fragile parsing, no chaining |

### The token-sequence point

Here is the part that surprises people. In a server with one tool, sloppy metadata still mostly works — there is nothing to confuse it with. In a server with fifteen tools, the tool definitions **compete for the model's attention inside a finite context window.**

A precise, well-scoped `description` acts as a strong retrieval signal during inference: when the user's phrasing aligns with it, the model's attention surfaces that tool. A vague description (`"Search documents"`, `"Get data"`) is low-signal noise. It does not align strongly with any particular user phrasing, so the model either overlooks it or fires it on the wrong intent. The tool is technically registered and completely unreliable.

**This is why metadata quality is a scaling problem, not a style preference.** It degrades exactly as your tool count grows — which is exactly when enterprise value appears.

---

## Part 2 — Data Setup (for the schema lessons)

The Input Schema and Output Schema lessons run against the **Titanic dataset** — the canonical public dataset for exactly this kind of teaching, with a clean mix of categorical and numeric columns.

Download the CSV (choose either):

- **No-friction mirror (recommended for this tutorial):** `https://www.kaggle.com/datasets/yasserh/titanic-dataset` — CC0 public domain, single CSV, no competition signup.
- **Official competition source:** `https://www.kaggle.com/c/titanic/data` — requires a Kaggle account and accepting the competition rules.

Place the file at `./data/titanic.csv` in the project folder.

**Column dictionary** (the columns the schema lessons use):

| Column | Type | Values / Notes |
|---|---|---|
| `Survived` | int | `0` = No, `1` = Yes |
| `Pclass` | int | `1`, `2`, `3` (ticket class — SES proxy) |
| `Sex` | string | `male`, `female` |
| `Age` | float | fractional if < 1; some rows blank |
| `SibSp` | int | siblings/spouses aboard |
| `Parch` | int | parents/children aboard |
| `Fare` | float | passenger fare |
| `Embarked` | string | `C` = Cherbourg, `Q` = Queenstown, `S` = Southampton |

The fixed, known set of values for `Pclass`, `Sex`, and `Embarked` is what makes this dataset ideal for an **enum** lesson — these are exactly the constraints the input schema should enforce.

---

## Part 3 — The Four Fields, Tool by Tool

We carry `hello_from_mcp` forward from Tutorial 01 as the **control specimen**: a tool with a name and description but no input parameters and only a primitive string return. Each new tool adds one dimension of metadata richness. The contrast against the control is deliberate — inspect them side by side and the lesson is visible in the Inspector UI itself.

### 3.0 — Baseline (carried from Tutorial 01)

```
Tool:        hello_from_mcp
Description: "Return a short greeting from the local MCP server."
Input:       none
Output:      str (primitive — no structured output schema)
```

Note what Inspector will show: a name, a description, an **empty input schema**, and **no meaningful output schema**. This is the floor. Everything below is what you gain by climbing off it.

---

### 3.1 — Lesson: NAME + DESCRIPTION (the disambiguation problem)

The single most common production failure is not a crash. It is the model confidently calling the *wrong* tool because two tools sound alike and their descriptions do not draw a hard boundary.

We model the sharpest version of this — **corpus confusion** — with two tools that share an identical name structure (`search_<corpus>`) but search entirely different document stores. (Both data sources here are illustrative; the lesson is the metadata wording, not the data.)

**Tool A — `search_resumes`**

```
Purpose:     Search the CANDIDATE RESUME store for people matching a query
             (skills, titles, experience).
Use when:    The user wants to FIND or shortlist PEOPLE / candidates.
Do NOT use:  to look up past company projects or proposals.
Input:       query (string, REQUIRED)
Output:      array of { candidate_id, name, headline, match_snippet, score }
```

**Tool B — `search_pds`** *(the confusable sibling)*

```
Purpose:     Search the PROJECT DATA SHEET store — records of the firm's PAST PROJECTS
             (scope, client, role, outcomes) used for proposals and BD.
Use when:    The user wants the firm's EXPERIENCE / past work on a topic.
Do NOT use:  to find people or candidates.
Input:       query (string, REQUIRED)
Output:      array of { pds_id, project_name, client, match_snippet, score }
```

#### Why this pair teaches the lesson

Ask the model: *"Find our experience with bridge inspection work."*

- With **weak descriptions** (`search_resumes`: "search documents" / `search_pds`: "search documents"), the two tools are indistinguishable. The model may fire `search_resumes` — returning *people*, not *projects* — and confidently answer the wrong question with a straight face. No error is thrown. The failure is silent and plausible, which is the worst kind.
- With **these descriptions**, each one states its corpus *and* a negative boundary (`Do NOT use to find people` / `Do NOT use to look up projects`). The model reads "experience / past work" → matches `search_pds`. The negative clause actively steers it away from the sibling.

Note also: `query` is **REQUIRED** on both. This is your first look at a required input — the model cannot invoke either tool without supplying a search string. (We return to required-vs-optional in §3.2.)

**Architect's takeaway:** Descriptions are not for humans browsing docs. They are decision-boundary specifications the model reasons over at inference time. Write them adversarially — assume a near-identical tool exists and state what this tool is *not* for. Corpus confusion is especially dangerous because it fails silently: wrong knowledge base, confident answer, no exception.

---

### 3.2 — Lesson: INPUT SCHEMA (the guardrail)

A loose input schema is an open door: the model will walk through it with whatever it guessed. A strict, typed schema forces the model to either construct a valid call or fail cleanly before any code executes.

Run against the Titanic CSV:

**Tool — `query_titanic_passengers`**

```
Purpose:     Return passenger rows matching optional filters.
Input contract:
  pclass      enum {1, 2, 3}            OPTIONAL
  sex         enum {"male","female"}    OPTIONAL
  embarked    enum {"C","Q","S"}        OPTIONAL
  min_age     number                    OPTIONAL
  max_age     number                    OPTIONAL
  survived    boolean                   OPTIONAL  (maps to 0/1 in data)
  limit       integer                   OPTIONAL  default 20, range 1–100
Output:      array of { passenger_id, name, pclass, sex, age, fare, survived }
```

#### Why the schema shape matters

The enums do the heavy lifting. Because `Pclass`, `Sex`, and `Embarked` have **fixed known values**, the schema can declare them as enums. Compare:

| Loose design | Strict design (above) |
|---|---|
| `pclass: string` | `pclass: enum {1,2,3}` |
| Model could pass `"first class"`, `"1st"`, `"upper"` | Model is *constrained* to `1`, `2`, or `3` |
| Server must normalize free text at runtime | Invalid value rejected at the boundary, before code runs |

Three more control signals in this one tool:

- **Type coercion as a contract.** `survived` is exposed as a `boolean` even though the data stores `0/1`. The schema documents the *interface* type; the implementation maps it. The model thinks in `true/false`; your code owns the translation.
- **Numeric range.** `limit` is an integer constrained to `1–100`. The model cannot request a million rows; the ceiling is part of the contract, not a runtime check you hope fires.
- **Optional with default.** Every filter is optional — omit them and you get an unfiltered sample capped at `limit`. The documented default (`20`) removes any guesswork about behavior when the model omits it.

**Architect's takeaway:** The input schema is where you move ambiguity from *runtime in your code* to *construction time in the model*. Enums over known value sets, narrow numeric ranges, and documented defaults are not cosmetic — they are the difference between a tool that rejects bad input at the boundary and one that silently does the wrong thing.

---

### 3.3 — Lesson: OUTPUT SCHEMA (the downstream contract)

Tutorial 01's tool returned a bare string. A string is fine for a human reading a greeting and useless for a system that must *do something* with the result. The output schema is the promise the tool makes to everything that consumes its return — the model itself (for chaining or citation) and any deterministic service downstream.

Run against the same Titanic CSV:

**Tool — `summarize_titanic_survival`**

```
Purpose:     Aggregate survival statistics grouped by one categorical column.
Input:       group_by  enum {"sex","pclass","embarked","survived"}  REQUIRED
Output contract (structured):
  group_by: string
  groups: array of {
    value          string    the category value (e.g., "female", "1")
    total          integer   passengers in this group
    survived       integer   how many survived
    survival_rate  number    survived / total, range 0.0–1.0
  }
```

#### Why structured output is the contract

If this tool returned a formatted string (`"female: 233/314 survived (74%)..."`), the consumer would have to *parse prose* to recover `survival_rate` for thresholding or `total` for weighting. That parsing breaks the moment the wording changes.

With a declared output schema:

- The **model** receives `structuredContent` it can reliably reference ("which group had the highest survival rate?" → it reads `groups` and compares `survival_rate`).
- A **downstream deterministic service** can feed `groups` straight into a chart or a rule (`survival_rate >= 0.5`) with zero natural-language processing.
- The **client validates** the return against the schema — a malformed result is caught at the boundary, not three services later.

Note `group_by` here is a **REQUIRED enum** — pairing the required-input lesson (§3.1) with the enum-constraint lesson (§3.2) on the input side, while the *return* delivers the output-schema lesson. One tool, both ends of the contract visible.

**Architect's takeaway:** Output schema is what makes a tool *composable* inside an enterprise system. Without it, every consumer reverse-engineers an undocumented format. With it, the tool is a typed component — which is the entire premise of using MCP instead of bespoke glue.

---

## Part 4 — How FastMCP Generates Each Metadata Field

Before generating the server, understand the *source* of each field. This is the mechanism that turns Python annotations into the metadata Inspector displays. It is also why your type hints and docstrings are not optional polish — they **are** the contract.

| Metadata field | Generated from | Concretely |
|---|---|---|
| `name` | `@mcp.tool(name=...)` or the function name | `@mcp.tool(name="search_pds")` |
| `description` | The function **docstring** | First lines of the docstring become the tool description |
| `inputSchema` | **Parameter type hints** (via Pydantic → JSON Schema) | `pclass: Literal[1,2,3] | None = None`, `limit: int = 20` |
| `outputSchema` | The **return type annotation** | Returning a Pydantic `BaseModel` / `TypedDict` generates a structured schema; returning bare `str` does not |

Two consequences worth internalizing:

1. **A missing docstring means a missing description** — the model loses its primary selection signal. Treat docstrings as production configuration.
2. **A primitive return annotation (`-> str`) yields no useful output schema.** To get the structured contract from §3.3, the tool must return a typed structure, which requires the structured-output support in `mcp >= 1.9.0`.

Enums map cleanly: a Python `Literal["male","female"]` becomes a JSON Schema `enum`, and `X | None = None` becomes an optional field. This is why the Titanic columns with fixed value sets are the right teaching vehicle.

---

## Part 5 — Generate the Server (Codex)

Consistent with Tutorial 01's workflow: specify the contract, let the coding agent implement. Paste the following prompt to Codex (or Claude Code) in the `02-tool-metadata` project folder.

```text
Expand the existing FastMCP server (server.py) from Tutorial 01.

Keep the existing setup:
- FastMCP over Streamable HTTP on 127.0.0.1:8000, path /mcp.
- host, port, streamable_http_path configured on the FastMCP constructor.
- Start with mcp.run(transport="streamable-http"); do not pass host/port/path to run().
- Keep the existing hello_from_mcp tool unchanged.
- main.py continues to start the same server object from server.py.

Dependencies (update pyproject.toml):
- mcp[cli] >= 1.9.0   (structured output support)
- pandas              (CSV reading)

Data:
- Read the Titanic CSV from a path in a module constant DATA_PATH = "./data/titanic.csv".
- Columns used: Survived (0/1), Pclass (1/2/3), Sex (male/female), Age (float, may be NaN),
  Fare (float), Embarked (C/Q/S), Name, PassengerId.
- Load the CSV once at import time into a pandas DataFrame; reuse it across calls.

For EVERY tool: a precise @mcp.tool(name=...), a docstring whose FIRST line states what it
does and when to use it (and, for the search pair, an explicit "Do NOT use ..." boundary),
fully type-hinted parameters, and a typed structured return (Pydantic BaseModel) so an
outputSchema is generated. Use Literal types for all enumerations. Mark optional params
with defaults.

Tool 1 — name "search_resumes"
  Docstring: Search the candidate resume store for people matching a query. Use when the
  user wants to FIND or shortlist candidates/people. Do NOT use to look up past projects.
  Param: query: str (REQUIRED).
  Return model ResumeHit list: candidate_id: str, name: str, headline: str,
  match_snippet: str, score: float.
  Implementation: return 3-5 realistic hard-coded sample candidates filtered by the query.

Tool 2 — name "search_pds"
  Docstring: Search the Project Data Sheet store of the firm's past projects. Use when the
  user wants the firm's EXPERIENCE / past work on a topic. Do NOT use to find people.
  Param: query: str (REQUIRED).
  Return model PdsHit list: pds_id: str, project_name: str, client: str,
  match_snippet: str, score: float.
  Implementation: return 3-5 realistic hard-coded sample projects filtered by the query.

Tool 3 — name "query_titanic_passengers"
  Docstring: Return Titanic passenger rows matching optional filters.
  Params (ALL optional unless noted):
    pclass: Literal[1,2,3] | None = None
    sex: Literal["male","female"] | None = None
    embarked: Literal["C","Q","S"] | None = None
    min_age: float | None = None
    max_age: float | None = None
    survived: bool | None = None   # maps to 0/1 in the data
    limit: int = 20                # clamp to range 1..100
  Return model PassengerRow list: passenger_id: int, name: str, pclass: int, sex: str,
  age: float | None, fare: float, survived: int.
  Implementation: filter the DataFrame by whichever params are provided; clamp limit to 1..100.

Tool 4 — name "summarize_titanic_survival"
  Docstring: Aggregate survival statistics grouped by one categorical column.
  Param: group_by: Literal["sex","pclass","embarked","survived"] (REQUIRED).
  Return model: group_by: str, groups: list of { value: str, total: int,
  survived: int, survival_rate: float }.
  Implementation: groupby the chosen column; survival_rate = survived/total rounded to 3 dp.

Prioritize correct names, docstrings, type hints, enum Literals, and structured return models
over implementation cleverness.
```

After Codex writes the files:

```bash
uv sync
uv run python server.py
```

Expected: the same startup banner as Tutorial 01 (Uvicorn on `127.0.0.1:8000`). Leave it running.

---

## Part 6 — Inspect Every Metadata Field in MCP Inspector

This is the core skill of Tutorial 02: validating the *contract*, independent of any AI client, before you ever wire the server to a model.

Start Inspector (no install required):

```bash
npx @modelcontextprotocol/inspector
```

Open `http://localhost:6274`. Set transport to **Streamable HTTP**, URL `http://127.0.0.1:8000/mcp`, click **Connect**, open the **Tools** tab.

You should now see five tools. Inspect them in this order — each step targets one metadata field.

### Step 1 — Inspect NAME

Read the tool names directly. Confirm `search_resumes` and `search_pds` appear as distinct identifiers. Ask the model's question: *from the name alone, could I tell these apart, and could I tell which corpus each searches?* The names alone hint at the distinction — the descriptions must seal it.

### Step 2 — Inspect DESCRIPTION

Select `search_resumes`; read the description Inspector shows — it is your docstring, verbatim, exactly as the model sees it. Then select `search_pds`. **Verify each states its corpus and a negative boundary.** If both could plausibly answer "find our bridge-inspection experience," the metadata is too weak — tighten the docstrings and re-sync. This is the single highest-leverage check in the tutorial.

### Step 3 — Inspect INPUT SCHEMA

Select `query_titanic_passengers`. Inspector renders the `inputSchema` (from your type hints) as a form and/or raw JSON Schema. Verify:

- `pclass`, `sex`, `embarked` show as **enums** with exactly their allowed values — not free strings.
- `survived` shows as **boolean** (even though the data is 0/1).
- `limit` shows as **integer** with its default and range.
- Every filter is **optional**; nothing is forced.

Then select `summarize_titanic_survival` and confirm `group_by` shows as a **REQUIRED enum**. Contrast: the query tool's filters are optional; this tool's single input is mandatory. The schema makes "required" visible and non-negotiable.

### Step 4 — Inspect OUTPUT SCHEMA

Select `summarize_titanic_survival`. Inspector shows the `outputSchema` derived from your return model — confirm the `groups` array with `value`, `total`, `survived`, `survival_rate` is present and typed.

**Now run the contrast:** select `hello_from_mcp`. It has **no meaningful output schema** — a bare string. Seeing them side by side is the lesson: the structured tool advertises a contract its consumers can rely on; the primitive tool offers a blob they must parse by hand.

### Step 5 — Execute and verify the round trip

For each tool, switch to its run panel, supply arguments, and click **Run**:

- `query_titanic_passengers` with `sex="female"`, `pclass=1` → rows come back matching the enum filters.
- `summarize_titanic_survival` with `group_by="sex"` → confirm `structuredContent` matches the declared output schema (female survival_rate noticeably higher than male — a known property of this dataset, and a quick sanity check that the aggregation is real).

This closes the loop: metadata declared (Steps 1–4) → metadata honored at runtime (Step 5).

> **Discipline:** Inspector validates the contract with zero model involvement. Always confirm metadata here *before* connecting a model. A tool that misbehaves in Inspector will misbehave worse behind an LLM — the model adds ambiguity, it never removes it.

---

## Part 7 — Enterprise Failure Modes (What This Prevents)

Translating the lessons into the production incidents they head off:

| Metadata weakness | Production failure | Business consequence |
|---|---|---|
| Confusable `search_*` names, no boundary in descriptions | Model searches the wrong corpus (people vs projects) | Confident, plausible, wrong answer — no exception thrown; erodes trust in the whole integration |
| Vague descriptions in a large toolset | Model under-uses correct tools, over-uses generic ones | Capability exists but is never invoked; ROI never materializes |
| Free-string inputs instead of enums | Model passes `"first class"` / `"1st"` / `"upper"` | Normalization burden and silent mismatches inside business logic |
| No output schema | Downstream services parse prose to extract fields | Brittle pipelines that break on any wording change |

The throughline for leadership: **MCP's enterprise value is that tools become typed, discoverable components.** That value is delivered entirely through metadata. Skip the metadata discipline and you have rebuilt bespoke integration glue with extra steps.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `FileNotFoundError` on startup | Titanic CSV missing | Download to `./data/titanic.csv` (see Part 2) |
| `ModuleNotFoundError: pandas` | dependency not synced | Add `pandas` to pyproject; `uv sync` |
| Tool appears but has no description | Missing/empty docstring | Add a docstring; first line = description; re-sync, restart |
| Enum field shows as plain string in Inspector | Param typed as `str`, not `Literal[...]` | Use `Literal[...]`; re-sync |
| `group_by` shows as optional | Parameter has a default value | Remove the default — required = no default |
| No `outputSchema` for a tool | Return annotation is primitive (`-> str`) | Return a Pydantic `BaseModel`; ensure `mcp >= 1.9.0` |
| Two search tools keep getting confused (model testing) | Descriptions lack a negative boundary | Add explicit "Do NOT use for…" to each docstring |
| Inspector can't connect | Wrong transport or server not running | Transport = `Streamable HTTP`; start server first |

---

## Key Takeaways

- An LLM does not call your tools — it reads their **metadata as text**, emits a request, and the client executes. Every metadata field is a control point in that loop.
- **Name + Description** decide tool *selection*. Corpus confusion (`search_resumes` vs `search_pds`) is the dangerous case because it fails silently. Write descriptions adversarially, with explicit negative boundaries.
- **Input Schema** decides what arguments are *permitted*. Enums over known value sets, numeric ranges, and documented defaults move ambiguity from your runtime to the model's construction step.
- **Output Schema** decides what consumers can *trust*. Structured returns make tools composable; primitive returns make them parse-and-pray.
- **MCP Inspector validates the contract with no model in the loop.** Inspect every field before connecting an LLM. The model adds ambiguity; it never subtracts it.
- Metadata quality is a **scaling problem** — it degrades precisely as tool count grows, which is precisely where enterprise value lives.

---

> **Next — Tutorial 03:** Connect this metadata-rich server to an actual LLM client and watch tool selection live — the same prompt, good vs. weak descriptions, and which tool the model picks. The payoff for everything inspected here.
