---
tutorial: "02 — Tool Metadata: The Contract Between LLM and Execution"
purpose: "Why a tool's name, description, inputSchema, and outputSchema are the control surface for LLM tool integration — and how to inspect each field with MCP Inspector."
audience: "New to MCP; lower-intermediate developer"
date: 2026-06-03
status: Draft
version: v5
prerequisite: "Tutorial 01 (Hello World) — a running FastMCP server over Streamable HTTP, inspected once."
---

# MCP Tutorial 02 — Tool Metadata
*The Contract Between LLM and Execution*

> Grab a cup of coffee. We're going to walk through this slowly, like a story, and by the end you'll see your tools the way the model sees them.

---

## What is MCP Metadata

**When the LLM has a dozen tools and an ambiguous user request, does it pick the right tool, build a valid call, and get back something the rest of the system can trust?**

Hold onto that question, because the whole tutorial is really just an answer to it.

Here's the surprising bit. You might think the answer lives inside your tools — in the clever code that runs when a tool fires. It doesn't. The answer lives in four tiny labels we stick on *every* tool before the model ever sees it:

- **`name`** — the tool's nametag. What do we call it?
- **`description`** — a little note that says "here's what I do, and here's when you'd want me."
- **`inputSchema`** — the rules for what you're allowed to hand the tool when you ask it to work.
- **`outputSchema`** — the promise about what shape the answer comes back in.

Now here's the idea I really want to land, so let me say it plainly. Think of these four labels not as *documentation* — not as a dusty instruction manual nobody reads — but as the **knobs and dials on a control panel.** They're how you tell the model what to do *without* rewiring its brain, without retraining it, and without crossing your fingers and hoping it guesses right. Get the labels right and the model behaves. Get them sloppy and you get exactly the messes that make a boss go "see, I *told* you the AI thing wouldn't work" — the wrong tool firing, garbage arguments, answers nothing downstream can read.

So that's our adventure: three little lessons, spread across four tools (plus the one friendly tool we already met in Tutorial 01). And to keep us honest, the schema lessons run against a **real public dataset** — real rows, real values — so we're constraining actual data instead of waving our hands at pretend examples.

---

## Part 1 — The Mechanism: How an LLM Actually "Sees" Your Tools

Let's clear up the biggest misunderstanding first, because almost everybody trips on it — and once you see it correctly, every decision later just *clicks*.

When folks imagine an AI "using a tool," they picture something like Lego bricks snapping together: the AI grabs your function and presses go, the way one piece of code calls another. It's a tidy picture. It's also completely wrong. So let me show you what's really happening behind the curtain.

### The actual lifecycle — told as five little beats

1. **Discovery — "what's in the toolbox?"** The MCP client knocks on the server's door and asks, "what have you got?" (the real message is called `tools/list`). The server hands back, for every tool, its four labels: `name`, `description`, `inputSchema`, and — if you defined one — `outputSchema`.
2. **Injection — "the model reads about the tools."** Now here's the part that surprises people. The client takes all those tool descriptions and *types them into the model's notebook* — its context window — as plain text, right next to your system prompt and the user's question. The model never *holds* your tools. It just reads a written description of them, like a kid reading the back of a toy box.
3. **Selection and arguments — "the model writes down what it wants."** When the user asks for something, the model does the only thing it knows how to do: it predicts what text should come next. And what comes out is a little request — a tool's name, plus a neat JSON bundle of arguments. That's all. The model doesn't *run* anything. It's matching the user's wish against the descriptions and rules it can see, and writing down its best guess at the order.
4. **Validation and execution — "the bouncer checks the order."** The client takes that request and checks the arguments against your `inputSchema`, like a bouncer checking IDs at the door. All good? It calls your actual function. Something's off? It can turn the request away *before a single line of your code runs*.
5. **Return — "the answer goes back into the notebook."** Your function's result — shaped by your `outputSchema` — gets written *back into the model's notebook* as more text, so the model can read it, quote it, or use it to decide the next step.

### So why does this make the labels so powerful?

Because every one of those four labels secretly controls one of the beats above. Watch:

| Field | What it really controls | What goes wrong when it's mushy |
|---|---|---|
| `name` | Which tool the model reaches for first | Two tools sound alike → it grabs the wrong one |
| `description` | *Whether and when* the model even thinks to use the tool | Vague note → tool gets ignored, or used for the wrong job |
| `inputSchema` | What the model is *allowed* to hand the tool | Loose rules → model makes up weird arguments → crashes, or worse, quiet wrongness |
| `outputSchema` | What the model and your other code can *count on* getting back | No promise → the answer's just a blob → everyone downstream has to squint and guess |

### The "everybody's shouting in one room" point

Here's the part that genuinely catches people off guard. If your server has *one* tool, sloppy labels barely matter — there's nobody to confuse it with. But picture fifteen tools. Now all fifteen descriptions are crammed into the same notebook, all kind of **shouting for the model's attention at once.**

A sharp, well-written `description` is like a clear, loud voice in that crowded room — when the user's question lines up with it, the model's attention turns straight toward that tool. A vague description (`"Search documents"`, `"Get data"`) is just mumbling in the corner. It doesn't line up with anything in particular, so the model either walks right past it or grabs it for the wrong job. The tool *exists*. It's *registered*. And it's utterly unreliable.

That's the big lesson of this whole part: **good labels aren't a matter of neatness — they're a matter of scale.** The mushiness only really bites once you have lots of tools... which is, of course, exactly the moment your project starts being worth something.

---

## Part 3 — The Four Fields, Tool by Tool

### 3.1 — Lesson: NAME + DESCRIPTION (telling near-twins apart)

Let me tell you about the scariest kind of failure — and it's scary precisely because *nothing breaks.* No red error. No crash. The model just confidently picks the *wrong* tool, because two tools sounded like twins and nobody told them apart clearly.

To show you the sharpest version of this — let's call it **the twins problem** — we build two tools with almost the same name shape (`search_<something>`), but they dig through completely different filing cabinets. (Don't worry about the data itself here; the whole lesson is in how we *word* the labels.)

**Tool A — `search_resumes`**

```
Purpose:     Search the CANDIDATE RESUME store for people matching a query
             (skills, titles, experience).
Use when:    The user wants to FIND or shortlist PEOPLE / candidates.
Do NOT use:  to look up past company projects or proposals.
Input:       query (string, REQUIRED)
Output:      array of { candidate_id, name, headline, match_snippet, score }
```

**Tool B — `search_pds`** *(the look-alike sibling)*

```
Purpose:     Search the PROJECT DATA SHEET store — records of the firm's PAST PROJECTS
             (scope, client, role, outcomes) used for proposals and BD.
Use when:    The user wants the firm's EXPERIENCE / past work on a topic.
Do NOT use:  to find people or candidates.
Input:       query (string, REQUIRED)
Output:      array of { pds_id, project_name, client, match_snippet, score }
```

#### Why these twins teach the lesson

Picture a user asking: *"Find our experience with bridge inspection work."*

- If both tools had **lazy descriptions** — say both just said "search documents" — they'd be identical twins in matching outfits. The model might grab `search_resumes` and hand back a list of *people* instead of *projects*, then cheerfully report the wrong answer with a perfectly straight face. No alarm goes off. And that calm, confident wrongness is honestly the worst thing that can happen.
- But with the descriptions above, each twin is wearing a name badge *and* a little sign that says what it's NOT for (`Do NOT use to find people` / `Do NOT use to look up projects`). The model reads "experience / past work," matches it to `search_pds`, and that "do not" line literally shoves it away from the wrong sibling.

One more thing to notice: `query` is marked **REQUIRED** on both. That's your very first peek at a required input — the model simply *cannot* knock on either tool's door without bringing a search string along. (We'll come back to required-vs-optional in §3.2.)

**The grown-up takeaway:** descriptions aren't notes for a human flipping through docs. They're the instructions the model actually reasons over, in the moment, to decide what to do. So write them a little paranoid — pretend an evil twin tool exists, and spell out what *this* tool is not for. The twins problem deserves the fear, because it fails so quietly: wrong cabinet, confident answer, zero errors.

---

### 3.2 — Lesson: INPUT SCHEMA (the guardrail on the road)

A loose input schema is like a road with no guardrails — the model will happily drive off the edge with whatever it guessed. A tight, typed schema is the guardrail: the model either stays on the road and builds a valid request, or it gets stopped cleanly *before* any of your code runs.

Now we point our tools at a real list — the Titanic passenger data:

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

#### Why the *shape* of the schema matters so much

The real heroes here are the **enums** — fancy word, simple idea: a short list of the *only* allowed answers. Because `Pclass`, `Sex`, and `Embarked` each have a small, fixed set of possible values, we can lock them down. Watch the difference:

| The sloppy way | The tight way (above) |
|---|---|
| `pclass: string` | `pclass: enum {1,2,3}` |
| Model might say `"first class"`, `"1st"`, `"upper"` | Model can *only* say `1`, `2`, or `3` |
| Your code has to clean up the mess later | Bad value is bounced at the door, before code runs |

And three more little control tricks are hiding in this one tool:

- **The "white lie" that's actually a contract.** We show `survived` to the model as a tidy `true/false`, even though the raw data stores `0/1`. The schema describes the *friendly outside* type; your code quietly handles the translation inside. The model gets to think in `true/false`; you own the plumbing.
- **A speed limit.** `limit` is a number, but it's fenced to `1–100`. The model can't suddenly ask for a million rows — that ceiling is baked into the contract, not some runtime check you're praying remembers to fire.
- **Optional, with a sensible default.** Every filter is optional. Leave them all out and you just get a small sample, capped at `limit`. And because we wrote the default down (`20`), there's no mystery about what happens when the model says nothing.

**The grown-up takeaway:** the input schema is where you move the guesswork *out* of your code and *into* the moment the model is building its request. Enums for known lists, sane number ranges, written-down defaults — none of that is decoration. It's the whole difference between a tool that politely refuses bad input and one that quietly does the wrong thing and smiles.

---

### 3.3 — Lesson: OUTPUT SCHEMA (the promise you make to whoever's next)

Remember Tutorial 01's little tool? It just handed back a plain string. That's perfectly fine when a human's reading a hello — and totally useless when a *machine* has to take that answer and *do* something with it. The output schema is the promise your tool makes to everyone who catches its result: the model itself (if it wants to keep going), and any other piece of software waiting downstream.

Same Titanic list, new tool:

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

#### Why a structured answer beats a pretty sentence

Imagine this tool just handed back a nice sentence: `"female: 233/314 survived (74%)..."`. Lovely for a human. But now picture the poor program downstream that needs the actual `survival_rate` number to make a decision — it has to *read the sentence like a detective* and fish the number out. And the second somebody reword that sentence even slightly, the detective falls apart.

Now picture it *with* a proper output schema instead:

- The **model** gets back tidy `structuredContent` it can trust. Ask "which group survived the most?" and it just reads the `groups` and compares the `survival_rate` numbers. Easy.
- A **plain old program** downstream can drop `groups` straight into a chart, or into a rule like `survival_rate >= 0.5`, without ever reading English.
- The **client double-checks** the result against the schema, so a broken answer gets caught right at the door — not three programs later when everything's on fire.

Quick note: `group_by` here is a **REQUIRED enum** — which neatly stacks the "required input" idea from §3.1 *and* the "enum" idea from §3.2 onto the input side, while the *return* shows off the output-schema idea. One little tool, both ends of the contract on display.

**The grown-up takeaway:** the output schema is what lets a tool *snap together* with the rest of an enterprise system like a building block. Skip it, and every program that touches your tool has to reverse-engineer some undocumented format. Include it, and your tool becomes a proper typed component — which, honestly, is the entire reason you're using MCP instead of hand-gluing everything together.

---

## Part 4 — Where Each Label Actually Comes From in FastMCP

Before we make the server, let's peek at *where* each of these four labels is born — because this is the magic trick that turns plain Python into the metadata Inspector shows you. And it's also why your type hints and docstrings aren't just tidy habits: they literally *are* the contract.

| The label | Born from | In plain terms |
|---|---|---|
| `name` | `@mcp.tool(name=...)`, or the function's name | `@mcp.tool(name="search_pds")` |
| `description` | The function's **docstring** | The first lines of the docstring become the description |
| `inputSchema` | Your **parameter type hints** (Pydantic turns them into JSON Schema) | `pclass: Literal[1,2,3] \| None = None`, `limit: int = 20` |
| `outputSchema` | Your **return type annotation** | Return a Pydantic `BaseModel` / `TypedDict` and you get a structured schema; return a bare `str` and you get nothing |

Two things really worth tattooing on your brain:

1. **No docstring means no description** — and no description means the model just lost its main clue for when to use the tool. So treat docstrings like real configuration, not afterthoughts.
2. **A plain `-> str` return gives you no useful output schema.** To get that lovely structured promise from §3.3, your tool has to return a proper typed structure — which needs the structured-output support in `mcp >= 1.9.0`.

And the enums map across beautifully: a Python `Literal["male","female"]` becomes a JSON Schema `enum`, and `X | None = None` becomes "this one's optional." That's exactly why those Titanic columns, with their small fixed sets of values, make such a perfect teaching toy.

---

## Part 5 — Build the Server (and Let Codex Do the Typing)

### Project Layout

Every tutorial in this series stands completely on its own. `02-tool-metadata` doesn't lean on `01-helloworld` or any other folder — it doesn't import from them, share a virtual environment, or touch their files. That's on purpose: one folder, one LinkedIn post, one video. Clean and self-contained.

```
learning-mcp/
└── 02-tool-metadata/
    ├── .python-version
    ├── main.py
    ├── pyproject.toml
    ├── server.py
    ├── uv.lock
    ├── data/
    │   └── titanic.csv
    └── .venv/
```

---

### Step 1 — Set Up the Project

In your VS Code terminal, hop into the `learning-mcp` root and make the new folder:

```bash
cd learning-mcp
mkdir 02-tool-metadata
cd 02-tool-metadata
```

Then get the standalone project going:

```bash
uv init --no-readme
uv venv
uv sync
```

Point VS Code at the `.venv` interpreter:
`Ctrl+Shift+P` → `Python: Select Interpreter` → pick `.venv`

---

### Step 2 — Drop in the Data

From inside `02-tool-metadata/`:

```bash
mkdir data
```

Copy `titanic.csv` into that `data/` folder, then make sure it's really there:

```bash
# Windows
dir data\titanic.csv

# macOS / Linux
ls -lh data/titanic.csv
```

You're looking for: file present, and not zero bytes.

---

### Step 3 — Let Codex Build the Server

> **One firm rule for Codex:** stay ONLY inside `02-tool-metadata/`. Don't open, read, import from, or touch `01-helloworld` or anything else in the repo.

The full set of instructions for Codex is a bit long, so it lives in its own file — that way you can copy the whole thing in one clean grab:

➡️ **[`codex_spec_tool_metadata_v1.txt`](./codex_spec_tool_metadata_v1.txt)**

Paste the entire contents into Codex (or Claude Code), with `02-tool-metadata/` set as the working folder, and let it do the typing.

---

### Step 4 — Sync and Run

Once Codex has written the files:

```bash
uv sync
uv run python server.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Leave that terminal alone — the server is now sitting there, quietly listening.

---

## Part 6 — Inspect Every Label with MCP Inspector

This is the real skill of Tutorial 02: checking the *contract* on its own — no AI client involved at all — *before* you ever hand the server to a model. Think of it as a dress rehearsal with no audience.

Fire up Inspector (nothing to install):

```bash
npx @modelcontextprotocol/inspector
```

Open `http://localhost:6274`. Set transport to **Streamable HTTP**, put in the URL `http://127.0.0.1:8000/mcp`, hit **Connect**, and open the **Tools** tab.

You should now see five tools. Walk through them in this order — each step puts one label under the microscope.

### Step 1 — Look at the NAME

Just read the names. Make sure `search_resumes` and `search_pds` show up as two clearly different things. Then play the model's game in your head: *from the name alone, could I tell these two apart — and could I tell which cabinet each one digs through?* The names give you a hint. The descriptions have to finish the job.

### Step 2 — Look at the DESCRIPTION

Click `search_resumes` and read the description Inspector shows you — that's your docstring, word for word, exactly as the model will read it. Now click `search_pds`. **Check that each one says which cabinet it searches AND what it's NOT for.** Here's your gut-check: if both could plausibly answer "find our bridge-inspection experience," your labels are still too mushy — tighten the docstrings and re-sync. Honestly, this one check is the single most valuable thing in the whole tutorial.

### Step 3 — Look at the INPUT SCHEMA

Click `query_titanic_passengers`. Inspector draws the `inputSchema` (built from your type hints) as a little form and/or raw JSON. Make sure:

- `pclass`, `sex`, `embarked` show up as **enums** with exactly their allowed values — not open-ended text boxes.
- `survived` shows up as a **boolean** (even though the data underneath is 0/1).
- `limit` shows up as an **integer** with its default and its range.
- Every filter is **optional** — nothing's being forced.

Then click `summarize_titanic_survival` and confirm `group_by` shows up as a **REQUIRED enum**. Feel the contrast: the query tool's filters were all "take it or leave it," but this tool's one input is "you must bring this." The schema makes "required" something you can actually *see* — and can't sneak past.

### Step 4 — Look at the OUTPUT SCHEMA

Click `summarize_titanic_survival`. Inspector shows the `outputSchema` it figured out from your return model — check that the `groups` array, with `value`, `total`, `survived`, and `survival_rate`, is all there and properly typed.

**Now do the side-by-side:** click `hello_from_mcp`. It has **no real output schema** — just a bare string. Seeing the two next to each other *is* the lesson: the structured tool is handing out a promise everyone can rely on, while the plain little tool hands out a blob that everyone downstream has to pick apart by hand.

### Step 5 — Run them and watch the round trip

For each tool, flip to its run panel, type in some arguments, and hit **Run**:

- `query_titanic_passengers` with `sex="female"`, `pclass=1` → back come the rows that match those enum filters.
- `summarize_titanic_survival` with `group_by="sex"` → check that the `structuredContent` matches the output schema you declared (and you'll notice the female survival rate sitting well above the male one — that's a famous fact about this data, and a quick way to know your math is real, not faked).

And that closes the loop nicely: you *declared* the labels (Steps 1–4), then you watched the tool actually *keep its promises* (Step 5).

> **A little discipline:** Inspector checks the contract with zero model in the picture. Always confirm everything here *before* you plug in a model. Why? Because a tool that misbehaves in Inspector will misbehave *worse* once a model's involved — the model only ever *adds* fuzziness to the situation; it never cleans it up.

---

## Part 7 — The Real-World Disasters This Quietly Prevents

Let me translate all this into the actual production fires you're putting out before they ever start:

| The sloppy label | The thing that breaks | What it costs the business |
|---|---|---|
| Twin `search_*` names, no "not for" line in the descriptions | Model digs through the wrong cabinet (people vs. projects) | A confident, believable, *wrong* answer — no error thrown — and trust in the whole system quietly leaks away |
| Vague descriptions in a big toolbox | Model ignores the right tools and over-leans on generic ones | The capability's right there, but it never gets used; the promised payoff never shows up |
| Open text inputs instead of enums | Model passes `"first class"` / `"1st"` / `"upper"` | Endless cleanup and silent mismatches buried deep in your business logic |
| No output schema | Downstream code reads sentences to fish out fields | Brittle pipelines that snap the moment any wording changes |

Here's the one line for the people in charge: **MCP's whole value is that your tools become typed, discoverable building blocks** — and that value rides entirely on the labels. Skip the label discipline, and you've just rebuilt the same old hand-glued integration mess, only with extra steps.

---

## Troubleshooting

| What you see | Why | The fix |
|---|---|---|
| `FileNotFoundError` on startup | The Titanic CSV isn't there | Put it at `./data/titanic.csv` |
| `ModuleNotFoundError: pandas` | Dependency wasn't synced | Add `pandas` to pyproject, then `uv sync` |
| Tool shows up but has no description | Docstring is missing or empty | Add a docstring — its first line becomes the description; re-sync and restart |
| An enum field shows as plain text in Inspector | You typed it as `str`, not `Literal[...]` | Use `Literal[...]`, then re-sync |
| `group_by` shows up as optional | The parameter has a default value | Remove the default — "required" means "no default" |
| A tool has no `outputSchema` | The return is a primitive (`-> str`) | Return a Pydantic `BaseModel`; make sure `mcp >= 1.9.0` |
| The two search tools keep getting confused (when testing with a model) | The descriptions are missing a "not for" line | Add an explicit "Do NOT use for…" to each docstring |
| Inspector won't connect | Wrong transport, or the server isn't running | Transport = `Streamable HTTP`; start the server first |

---

## Key Takeaways

- An LLM doesn't really *call* your tools — it *reads* their labels as text, writes down a request, and the client does the actual running. Every label is a knob on that loop.
- **Name + Description** decide *which* tool gets picked. The twins case (`search_resumes` vs `search_pds`) is the dangerous one, because it fails without a peep. So write descriptions a little paranoid, with a clear "not for this" line.
- **Input Schema** decides what arguments are even *allowed*. Enums for known lists, sane number ranges, written-down defaults — they shove the guesswork out of your code and into the model's request-building step.
- **Output Schema** decides what everyone downstream can *trust*. Structured answers snap together like building blocks; bare strings leave everyone playing detective.
- **MCP Inspector checks the contract with no model in the loop.** Inspect every label before you connect an LLM. The model only adds fog; it never clears it.
- And the big one: good labels are a **scaling thing** — the mush only bites once you have lots of tools, which is exactly where the real value lives.

---

> **Coming up — Tutorial 03:** we finally plug this label-rich server into a real LLM and watch it pick tools *live* — same question, good descriptions vs. weak ones, and which tool it grabs. That's the payoff for everything we just inspected.
