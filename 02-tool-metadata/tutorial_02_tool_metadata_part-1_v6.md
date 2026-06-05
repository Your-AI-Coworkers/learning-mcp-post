

# MCP Tutorial 02 — Tool Metadata
*The Contract Between LLM and Execution*

Grab a cup of coffee. We're going to walk through this slowly, like a story, and by the end you'll see your tools the way the model sees them.

---

## **THEORY** What is MCP Metadata

**When the LLM has a dozen tools and an ambiguous user request, does it pick the right tool, build a valid call, and get back something the rest of the system can trust?**

Hold onto that question, because the whole tutorial is really just an answer to it.

Here's the surprising bit. You might think the answer lives inside your tools — in the clever code that runs when a tool fires. It doesn't. The answer lives in **four tiny labels we stick on** *every* tool before the model ever sees it:

1. **NAME** — the tool's nametag. What do we call it?
2. **DESCRIPTION** — a little note that says "here's what I do, and here's when you'd want me."
3. **INPUT SCHEMA** — the rules for what you're allowed to hand the tool when you ask it to work.
4. **OUTPUT SCHEMA** — the promise about what shape the answer comes back in.

Now here's the idea I really want to land, so let me say it plainly. Think of these four labels not as *documentation* — not as a dusty instruction manual nobody reads — but as the **knobs and dials on a control panel.** They're how you tell the model what to do *without* rewiring its brain, without retraining it, and without crossing your fingers and hoping it guesses right. Get the labels right and the model behaves. Get them sloppy and you get exactly the messes that make a boss go "see, I *told* you the AI thing wouldn't work" — the wrong tool firing, garbage arguments, answers nothing downstream can read.

So that's our adventure: three little lessons, spread across four tools (plus the one friendly tool we already met in Tutorial 01). And to keep us honest, the schema lessons run against a **real public dataset** — real rows, real values — so we're constraining actual data instead of waving our hands at pretend examples.

---

## The Mechanism: How an LLM Actually "Sees" Your Tools

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




</BR></BR></BR></BR></BR></BR></BR></BR>




## **LAB** Bad Tools vs Good Tools

Here is the whole lab in one sentence: **the implementation doesn't change. The metadata does. And the behaviour changes completely.**

Two files. Four tools each. Open them side by side.

| File | Role |
|---|---|
| `mcp-server-bad-tools.py` | Four tools with careless metadata — names, descriptions, types, output shapes all chosen poorly |
| `mcp-server-good-tools.py` | The same four tools — every if-block, loop, and computation byte-for-byte identical — only the contracts repaired |

The four tools and the lesson each one carries:

| Tool (bad name → good name) | Data | Lesson |
|---|---|---|
| `hello_from_mcp` | — | Tutorial 01 friend, unchanged in both files |
| `search` → `search_countries` | countries.csv | Name + Description |
| `get` → `filter_countries` | countries.csv | Name + Description, Input Schema |
| `query_titanic_passengers` | titanic.csv | Input Schema |
| `summarize_titanic_survival` | titanic.csv | Output Schema |

**Getting the data.** Drop both CSV files into a `data/` folder alongside the two server files.

- `titanic.csv` — same file from Tutorial 01
- `countries.csv` — download *countries-of-the-world-2023* from [Kaggle (nelgiriyewithana)](https://www.kaggle.com/datasets/nelgiriyewithana/countries-of-the-world-2023). The server reads five columns from it: `Country`, `Continent`, `Population`, `Land Area(Km2)`, `Capital/Major City`.

---

### 3.1 — Lesson: NAME + DESCRIPTION (the twins problem, made real)

Let me remind you what the twins problem looks like before we build it.

A model picks tools by reading their names and descriptions in one sitting and trying to match whatever the user just said. If two tools sound alike — same verb family, similar description, same output shape — the model is guessing. And it will guess wrong half the time, silently, with complete confidence.

The two countries tools in `mcp-server-bad-tools.py` are textbook twins:

**Tool A — `search` (bad)**

```
name:         search
description:  Search data.
input:        query  string  REQUIRED
output:       array of country records
```

**Tool B — `get` (bad)**

```
name:         get
description:  Get records.
input:        continent  string  OPTIONAL
              min_population  integer  OPTIONAL
              max_population  integer  OPTIONAL
              limit  integer  OPTIONAL
output:       array of country records
```

Now put yourself in the model's seat. A user says: *"Show me countries in Asia with a population over 100 million."* Is that a `search` problem or a `get` problem? From the descriptions, there is absolutely no way to know. Both return country records. One says "search data." The other says "get records." The model has to guess — and it might fire `search` with `query = "Asia population 100 million"` and get a text-match result that has nothing to do with population filtering. No alarm goes off. The tool ran. The answer is wrong. Everybody moves on.

Now open `mcp-server-good-tools.py`:

**Tool A — `search_countries` (good)**

```
name:         search_countries
description:  Search for countries by name, capital city, or continent keyword.
              Use when the user names or partially describes a country
              (e.g. "France", "countries near the Alps", "African nations").
              Do NOT use to filter by numeric criteria such as population or area.
input:        query  string  REQUIRED — a country name, city, or descriptive phrase
output:       array of matching country records
```

**Tool B — `filter_countries` (good)**

```
name:         filter_countries
description:  Filter countries by structured criteria: continent, population range.
              Use when the user wants to narrow down countries by measurable attributes
              (e.g. "largest countries in Asia", "countries with more than 50 million people").
              Do NOT use for free-text name or city lookup — use search_countries instead.
input:        continent       enum  OPTIONAL — Africa | Asia | Europe |
                                              North America | South America | Oceania
              min_population  integer  OPTIONAL
              max_population  integer  OPTIONAL
              limit           integer  OPTIONAL  default 10, max 100
output:       array of matching country records
```

The names alone do half the work — `search_countries` vs `filter_countries` signal two genuinely different operations. The descriptions do the rest: each one says exactly what the user request looks like that should trigger it, and what the *other* tool handles. Now the question *"countries in Asia with population over 100 million"* is unambiguous: measurable attribute filter → `filter_countries`, `continent="Asia"`, `min_population=100000000`. No guess required.

One side effect worth noticing: `continent` in the good version is now an **enum** — six fixed options instead of a free string. That's the first glimpse of input schema work, which we'll dig into fully in the next lesson.

**The grown-up takeaway:** descriptions aren't notes for a human flipping through docs. They're the instructions the model reasons over, in real time, to decide what to do. So write them a little paranoid — pretend an evil twin exists, and spell out what *this* tool is not for. The `Do NOT use` clause isn't defensive overkill. It's the single most useful sentence you'll write, because it's the only explicit shove away from the wrong sibling.

---

### 3.2 — Lesson: INPUT SCHEMA (guardrails on the way in)

A loose input schema is a road with no guardrails. The model will drive off the edge with whatever it guessed, and your code won't know until something crashes — or worse, silently returns wrong data.

The guardrail lesson runs across two tools: `filter_countries` and `query_titanic_passengers`. Both have parameters with a small, fixed set of valid values — perfect candidates for the tightest kind of input constraint: the **enum.**

Look at the bad versions of their filter parameters:

**`get` (bad) — continent as free string**

```
continent:  string  OPTIONAL
```

The model might send `"europe"`, `"EUROPE"`, `"eu"`, `"European continent"`. The code compares against exact DataFrame values. Most of those miss. No error fires. The filter just returns everything or nothing, silently.

**`query_titanic_passengers` (bad) — untyped critical fields**

```
pclass:    integer  OPTIONAL    ← model can send 0, 4, or 999
sex:       string   OPTIONAL    ← "Male", "M", "woman" all pass the schema
embarked:  string   OPTIONAL    ← "Southampton", "S port" both look fine
survived:  integer  OPTIONAL    ← 0/1 is implicit; model might try 2 or -1
```

None of these will raise a schema validation error. The values simply won't match any rows, and the tool returns an empty list that looks like a correct empty result. The model reports no survivors in first class, because it asked for `pclass=1st` and the DataFrame only knows `1`.

Now look at the good versions:

**`filter_countries` (good) — continent as enum**

```
continent:  enum  OPTIONAL
            Africa | Asia | Europe | North America | South America | Oceania
```

The model can *only* send one of those six strings. Anything else is rejected by the schema validator before your code runs. The casefold mismatch problem disappears because there's no longer a range of things to mismatch.

**`query_titanic_passengers` (good) — every categorical field locked down**

```
pclass:    enum {1, 2, 3}              OPTIONAL
sex:       enum {"male", "female"}     OPTIONAL
embarked:  enum {"C", "Q", "S"}        OPTIONAL
survived:  boolean                     OPTIONAL  (mapped to 0/1 inside the tool)
limit:     integer  default 20, max 100
```

Three things are hiding in this one tool that are worth naming:

- **The clean-interface trick.** We expose `survived` as a `boolean` even though the raw data is `0/1`. The schema describes the *friendly outside* type; the code quietly handles the translation inside with `int(survived)`. The model thinks in `true/false`; you own the plumbing.
- **The speed limit.** `limit` isn't a raw number — the description documents its ceiling. The model knows not to ask for a million rows because the contract says the ceiling is 100.
- **Enum over string, always.** When a field has a small, fixed set of valid values — class, sex, port code, category label — the default should always be a `Literal` type. The cost is two extra characters. The benefit is that bad values get bounced at the door, before a single line of your filtering code runs.

**The grown-up takeaway:** the input schema is where you move the guesswork *out* of your code and *into* the moment the model is building its request. Enums for known lists, written-down defaults, documented ceilings — none of that is decoration. It's the whole difference between a tool that politely bounces bad input and one that quietly does the wrong thing and smiles.

---

### 3.3 — Lesson: OUTPUT SCHEMA (the promise you make to whoever's next)

The output schema is the promise your tool makes to everyone who touches its result: the model itself (if it wants to keep reasoning), and any program downstream that needs to actually use the number.

The output schema lesson lives in `summarize_titanic_survival`. Compare the two versions:

**Bad — returns `str`**

```
output:  string
```

What the model actually gets back:

```
female: 233/314 survived (74.2%)
male: 109/577 survived (18.9%)
```

That's a perfectly readable sentence for a human. It is almost useless for a machine. If the model wants to answer "which group survived more?" it has to *read the sentence* and extract numbers from English text. If another program downstream needs the female survival rate as a number, it has to parse that string — and the moment someone rewrites the format, the parser breaks. No alarm fires because the tool worked; the data just arrived in a shape nobody could easily consume.

**Good — returns `SurvivalSummary`**

```
output:
  group_by:  string           — column used for grouping, e.g. "sex"
  groups:    array of {
    value:          string    — the category value, e.g. "female", "1", "C"
    total:          integer   — total passengers in this group
    survived:       integer   — number who survived
    survival_rate:  number    — fraction who survived, range 0.0–1.0
  }
```

Now picture the same downstream question — "which group survived more?" The model doesn't have to parse English. It reads `groups`, compares `survival_rate` numbers, and answers. A plain program can drop `groups` directly into a chart. A rule like `survival_rate >= 0.5` writes itself. And the client double-checks the result shape against the schema at the door, so a broken return gets caught immediately.

There's also a second dimension of output schema quality that you'll see in `mcp-server-good-tools.py`: **Field descriptions.** In the bad file, the Pydantic models have no `Field(description=...)`. In the good file, every field carries one:

```python
# bad
class SurvivalGroup(BaseModel):
    value: str
    survival_rate: float

# good
class SurvivalGroup(BaseModel):
    value:         str   = Field(description="The category value, e.g. 'female', '1', 'C'")
    survival_rate: float = Field(description="Fraction who survived, range 0.0–1.0")
```

Those Field descriptions get injected into the JSON schema the model reads. Without them, the model sees `survival_rate: number` and makes an educated guess about the units and range. With them, it reads "fraction who survived, range 0.0–1.0" and knows exactly what to do with the number. It's the difference between handing someone a labelled bottle and handing them an unlabelled one.

**The grown-up takeaway:** the output schema is what lets a tool snap together with the rest of a system like a building block. Skip it, and every program that touches your tool has to reverse-engineer an undocumented format. Include it — with typed fields and Field descriptions — and your tool becomes a proper typed component, usable by the model *and* by machines downstream without a human translator in between.

---



## Key Takeaways

- An LLM doesn't really *call* your tools — it *reads* their labels as text, writes down a request, and the client does the actual running. Every label is a knob on that loop.
- **Name + Description** decide *which* tool gets picked. The twins case (`search` vs `get`) is the dangerous one, because it fails without a peep. Write descriptions a little paranoid, with a clear "not for this" line.
- **Input Schema** decides what arguments are even *allowed*. Enums for known lists, documented defaults and ceilings — they shove the guesswork out of your code and into the model's request-building step.
- **Output Schema** decides what everyone downstream can *trust*. A typed Pydantic return with Field descriptions is the difference between a labelled component and an unlabelled blob.
- **MCP Inspector checks the contract with no model in the loop.** Inspect every label before you connect an LLM. The model only adds fog; it never clears it.
- And the big one: good labels are a **scaling thing** — the mush only bites once you have lots of tools, which is exactly where the real value lives.

---

> **Coming up — Tutorial 03:** we finally plug this label-rich server into a real LLM and watch it pick tools *live* — same question, good descriptions vs. weak ones, and which tool it grabs. That's the payoff for everything we just inspected.
