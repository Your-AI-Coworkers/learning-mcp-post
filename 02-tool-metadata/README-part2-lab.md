

# **LAB** — Bad Tools vs Good Tools

Here is the whole lab in one sentence: **the implementation doesn't change. The metadata does. And the behaviour changes completely.**

We have two files — `countries_tools.py` (the data-access layer: SQL, queries, returns) and `countries_tool_registration.py` (the `register()` function that wraps those queries as MCP tools). Over the next four lessons we'll leave every line of SQL, every query function, every return statement in `countries_tools.py` exactly as it is. The only things we touch are the four labels from Part 1: **name**, **description**, **inputSchema**, and **outputSchema** — all inside `countries_tool_registration.py`. By the end you'll be able to read a `tools/list` dump the way a mechanic reads an engine — and spot the misfire before anything breaks.

---

## Quick Tour of the Data

The dataset is a CSV of **227 countries** with 20 columns — population, GDP, literacy rate, region, and so on. Real rows, real values, sourced from a well-known public dataset.


---

## The "Lazy Friday" Version

Here's what the tools look like right now — the version you'd write at 4:55 PM on a Friday when you just want something that works:

```python
# countries_tool_registration.py

from countries_tools import country_count, get_country, search_countries


def register(mcp) -> None:
    @mcp.tool()
    def country_count_tool() -> int:
        """Return the number of rows in the countries SQLite database."""
        return country_count()

    @mcp.tool()
    def search_countries_tool(name_like: str) -> list[dict[str, str]]:
        """Search countries by partial name match."""
        return search_countries(name_like)

    @mcp.tool()
    def get_country_tool(country: str) -> dict[str, str] | None:
        """Return a single country row by exact country name."""
        return get_country(country)
```

It runs. It passes manual tests. Ship it.

But here's the thing — you're not the one who has to *use* these tools. A language model is. And the model never sees your Python. It sees this:

### What the model actually receives

When a client calls `tools/list`, FastMCP auto-generates JSON from your function signature and docstring. Here's what the model gets for `search_countries_tool`:

```json
{
  "name": "search_countries_tool",
  "description": "Search countries by partial name match.",
  "inputSchema": {
    "properties": {
      "name_like": {
        "title": "Name Like",
        "type": "string"
      }
    },
    "required": ["name_like"],
    "type": "object"
  }
}
```

Read that slowly. Pretend you're the model, and you've got 15 tools crammed into your context window. A user asks: *"What's the population of France?"*

You see two tools that sound relevant: `search_countries_tool` ("Search countries by partial name match") and `get_country_tool` ("Return a single country row by exact country name"). Which do you pick? What do you pass? The descriptions are so terse they're almost interchangeable. The input schemas tell you nothing about what a valid value looks like — just "give me a string."

This is the gap. The code works perfectly. The metadata is sleepwalking.

---

## Lesson 1: Name — From Collision to Carve-Out

The current names:

| Tool | Name |
|---|---|
| Count rows | `country_count_tool` |
| Fuzzy search | `search_countries_tool` |
| Exact lookup | `get_country_tool` |

Three problems. First, `_tool` is noise — every tool is a tool, that suffix tells the model nothing. Second, `search_countries` and `get_country` are dangerously similar in a crowded context window. Is "get" an exact match or just a fetch? Is "search" fuzzy or exact? The model has to guess. Third, the names don't hint at *what kind* of operation each one is.

### The fix

```python
@mcp.tool()
def count_countries() -> int:
    ...

@mcp.tool()
def search_countries_by_name(name_like: str) -> ...:
    ...

@mcp.tool()
def lookup_country(country: str) -> ...:
    ...
```

Now the names carve out territory:

- **`count_countries`** — clearly a count, no arguments expected. The model won't reach for this when the user asks about a specific country.
- **`search_countries_by_name`** — the word *search* signals "partial, might return many," and *by_name* tells you what the filter is.
- **`lookup_country`** — *lookup* signals "I already know the exact key, give me the record." Distinct from *search* in exactly the way a dictionary is distinct from a search engine.

The model now has three names that don't compete. Each one wins a different kind of question — and loses gracefully when the question doesn't match.

---

## Lesson 2: Description — From Mumbling to Clear Voice

Here are the current descriptions (pulled straight from the docstrings):

| Tool | Description |
|---|---|
| `country_count_tool` | "Return the number of rows in the countries SQLite database." |
| `search_countries_tool` | "Search countries by partial name match." |
| `get_country_tool` | "Return a single country row by exact country name." |

Remember the "everybody's shouting in one room" point from Part 1? These descriptions are mumbling. They state the *what* but never the *when*. The model knows what each tool does, but not **when to reach for one over the other** — which is the whole decision it needs to make.

### The fix

Write descriptions that answer three questions: **What do I do? When should you pick me? What do I give back?**

```python
@mcp.tool()
def count_countries() -> int:
    """Return the total number of countries in the database.

    Use this tool when the user asks how many countries exist,
    wants a total count, or needs to know the size of the dataset.
    Returns a single integer.
    """
    return country_count()

@mcp.tool()
def search_countries_by_name(name_like: str) -> list[dict[str, str]]:
    """Search for countries whose name contains the given text (case-insensitive, partial match).

    Use this tool when the user gives a partial or uncertain country name —
    e.g. 'stan', 'united', 'new' — and expects multiple possible matches.
    Returns up to 25 matching country records, each with 20 fields
    including population, GDP, literacy rate, and region.
    """
    return search_countries(name_like)

@mcp.tool()
def lookup_country(country: str) -> dict[str, str] | None:
    """Retrieve the full record for one country by its exact official name.

    Use this tool when the user names a specific country and wants its details —
    e.g. 'France', 'Brazil', 'Japan'. Requires the exact country name as stored
    in the database. Returns one record with 20 fields (population, GDP,
    literacy, region, etc.) or null if no match is found.
    If uncertain about the exact spelling, use search_countries_by_name first.
    """
    return get_country(country)
```

Notice the last line in `lookup_country`'s description: *"If uncertain about the exact spelling, use search_countries_by_name first."* That's **tool choreography** — you're telling the model how to chain tools. The model can now build a two-step plan: search first, then look up the exact match. That decision logic lives entirely in the metadata, not in the code.

### What changed in the JSON

The `description` field went from one sentence to a paragraph. Everything else in the `tools/list` output stays identical. The model's decision surface just got dramatically sharper — for zero lines of implementation change.

---

## Lesson 3: Input Schema — The Bouncer Gets a Guest List

Here's what the model currently sees for `search_countries_tool`'s input:

```json
"properties": {
  "name_like": {
    "title": "Name Like",
    "type": "string"
  }
},
"required": ["name_like"]
```

That's it. A required string called `name_like`. No hint about what values are valid. No description of what the parameter means. The model is left to infer everything from the parameter name alone — and `name_like` is SQL jargon that a language model might or might not recognize as "partial match."

Now, with plain Python type hints and docstrings (no Pydantic `Field()` yet), we can't add parameter-level descriptions or constraints directly into the JSON schema. But we *can* do two important things:

### 3a. Better parameter names

A parameter named `name_like` is a leaked implementation detail — it tells the model about SQL `LIKE`, not about what the user is typing. Rename it:

```python
def search_countries_by_name(name_fragment: str) -> list[dict[str, str]]:
```

Now the schema says `"name_fragment": {"type": "string"}` — clearer, though still minimal.

### 3b. Parameter guidance in the description

Since plain type hints don't carry descriptions into the JSON schema, the tool description does double duty. Look at how the improved descriptions from Lesson 2 already handle this — *"the user gives a partial or uncertain country name — e.g. 'stan', 'united', 'new'"*. Those examples in the description act as implicit input constraints. The model learns what kind of strings to pass, even though the JSON schema itself just says `"type": "string"`.

### What about a region filter?

Suppose we wanted to add a region filter to the search. With plain type hints, we'd write:

```python
from typing import Literal

REGIONS = Literal[
    "ASIA (EX. NEAR EAST)",
    "BALTICS",
    "C.W. OF IND. STATES",
    "EASTERN EUROPE",
    "LATIN AMER. & CARIB",
    "NEAR EAST",
    "NORTHERN AFRICA",
    "NORTHERN AMERICA",
    "OCEANIA",
    "SUB-SAHARAN AFRICA",
    "WESTERN EUROPE",
]

@mcp.tool()
def search_countries_by_name(
    name_fragment: str,
    region: REGIONS | None = None,
) -> list[dict[str, str]]:
```

Now look at what happens to the JSON schema:

```json
"properties": {
  "name_fragment": {
    "title": "Name Fragment",
    "type": "string"
  },
  "region": {
    "anyOf": [
      {
        "enum": [
          "ASIA (EX. NEAR EAST)",
          "BALTICS",
          "C.W. OF IND. STATES",
          "EASTERN EUROPE",
          "LATIN AMER. & CARIB",
          "NEAR EAST",
          "NORTHERN AFRICA",
          "NORTHERN AMERICA",
          "OCEANIA",
          "SUB-SAHARAN AFRICA",
          "WESTERN EUROPE"
        ],
        "type": "string"
      },
      { "type": "null" }
    ],
    "default": null,
    "title": "Region"
  }
},
"required": ["name_fragment"]
```

*That's* the bouncer with a guest list. The model can't invent a region — it can only pick from the eleven values the schema permits. An invalid value gets rejected before your code ever runs. And because `region` has a `default` of `null`, the model knows it's optional — it won't hallucinate a region when the user didn't mention one.

This is as far as Python's built-in type hints take you. The bouncer has a guest list, but no clipboard with notes about each guest. In a future part of this series, we'll bring in Pydantic `Field()` and give each parameter its own description, validation rules, and examples — right inside the JSON schema.

---

## Lesson 4: Output Schema — The Promise

Here's what FastMCP currently auto-generates as the output schema for `search_countries_tool`:

```json
{
  "properties": {
    "result": {
      "items": {
        "additionalProperties": { "type": "string" },
        "type": "object"
      },
      "title": "Result",
      "type": "array"
    }
  },
  "required": ["result"],
  "title": "search_countries_toolOutput",
  "type": "object"
}
```

Translation: "You'll get an array of objects. Each object has... some string keys. Good luck."

The model knows it'll receive a list of dictionaries, but has no idea what keys to expect. It can't tell the user "France has a GDP of $24,000" with confidence — it has to *hope* there's a key called `GDP ($ per capita)` in whatever comes back. And downstream code that tries to parse the result? It's flying blind.

### The fix — TypedDict

Python's `TypedDict` lets us name the keys without changing the return value:

```python
from typing_extensions import TypedDict  # use typing.TypedDict on Python 3.12+

class CountryRecord(TypedDict):
    Country: str
    Region: str
    Population: str
    Area_sq_mi: str
    Pop_Density_per_sq_mi: str
    Coastline_coast_area_ratio: str
    Net_migration: str
    Infant_mortality_per_1000_births: str
    GDP_per_capita: str
    Literacy_pct: str
    Phones_per_1000: str
    Arable_pct: str
    Crops_pct: str
    Other_pct: str
    Climate: str
    Birthrate: str
    Deathrate: str
    Agriculture: str
    Industry: str
    Service: str
```

Now the return type annotation changes:

```python
def search_countries_by_name(name_fragment: str) -> list[CountryRecord]:
    ...

def lookup_country(country: str) -> CountryRecord | None:
    ...
```

And the output schema transforms from "array of mystery objects" to a fully enumerated contract — every key named, every type declared. The model knows exactly what fields exist in each record, and downstream code can parse the result without guessing.

> **A practical note:** The raw CSV column names have spaces and parentheses (`"GDP ($ per capita)"`), so the `TypedDict` keys above are sanitized versions. In your actual data layer you'd either clean the column names on import, or map between the raw names and the typed names. The point isn't the exact key names — it's that the schema *has* key names at all, instead of `additionalProperties: {"type": "string"}`.

---

## The "Good Monday" Version — Side by Side

Here's the before and after, measured in what the model sees:

### Before (Lazy Friday)

```
tools/list response:
┌────────────────────────┬───────────────────────────────────────────────┐
│ name                   │ description                                   │
├────────────────────────┼───────────────────────────────────────────────┤
│ country_count_tool     │ Return the number of rows in the countries    │
│                        │ SQLite database.                              │
├────────────────────────┼───────────────────────────────────────────────┤
│ search_countries_tool  │ Search countries by partial name match.       │
├────────────────────────┼───────────────────────────────────────────────┤
│ get_country_tool       │ Return a single country row by exact country  │
│                        │ name.                                         │
└────────────────────────┴───────────────────────────────────────────────┘

Input schemas:  bare "type": "string", no constraints
Output schemas: "additionalProperties": {"type": "string"} — opaque blobs
```

### After (Good Monday)

```
tools/list response:
┌──────────────────────────────┬───────────────────────────────────────────┐
│ name                         │ description (excerpt)                      │
├──────────────────────────────┼───────────────────────────────────────────┤
│ count_countries              │ Total count of countries. Use when user    │
│                              │ asks "how many countries..."               │
├──────────────────────────────┼───────────────────────────────────────────┤
│ search_countries_by_name     │ Partial name match. Use when user gives    │
│                              │ a fragment like 'stan' or 'united'.        │
│                              │ Returns up to 25 records with 20 fields.   │
├──────────────────────────────┼───────────────────────────────────────────┤
│ lookup_country               │ Exact name lookup. Use when user names a   │
│                              │ specific country. If unsure of spelling,   │
│                              │ use search_countries_by_name first.        │
└──────────────────────────────┴───────────────────────────────────────────┘

Input schemas:  descriptive parameter names, Literal enums for region,
                optional params with defaults
Output schemas: TypedDict with all 20 field names declared
```

**Same three functions. Same SQL. Same results.** The only difference is how clearly the tools introduce themselves — and that difference is the entire gap between a model that picks the right tool confidently and one that flips a coin.

---

### Appendix: Full "Good Monday" countries_tool_registration.py

```python
# countries_tool_registration.py

from __future__ import annotations

from typing import Literal
from typing_extensions import TypedDict  # use typing.TypedDict on Python 3.12+

from countries_tools import country_count, get_country, search_countries


REGIONS = Literal[
    "ASIA (EX. NEAR EAST)",
    "BALTICS",
    "C.W. OF IND. STATES",
    "EASTERN EUROPE",
    "LATIN AMER. & CARIB",
    "NEAR EAST",
    "NORTHERN AFRICA",
    "NORTHERN AMERICA",
    "OCEANIA",
    "SUB-SAHARAN AFRICA",
    "WESTERN EUROPE",
]


class CountryRecord(TypedDict):
    Country: str
    Region: str
    Population: str
    Area_sq_mi: str
    Pop_Density_per_sq_mi: str
    Coastline_coast_area_ratio: str
    Net_migration: str
    Infant_mortality_per_1000_births: str
    GDP_per_capita: str
    Literacy_pct: str
    Phones_per_1000: str
    Arable_pct: str
    Crops_pct: str
    Other_pct: str
    Climate: str
    Birthrate: str
    Deathrate: str
    Agriculture: str
    Industry: str
    Service: str


def register(mcp) -> None:
    @mcp.tool()
    def count_countries() -> int:
        """Return the total number of countries in the database.

        Use this tool when the user asks how many countries exist,
        wants a total count, or needs to know the size of the dataset.
        Returns a single integer.
        """
        return country_count()

    @mcp.tool()
    def search_countries_by_name(
        name_fragment: str,
        region: REGIONS | None = None,
    ) -> list[CountryRecord]:
        """Search for countries whose name contains the given text (case-insensitive, partial match).

        Use this tool when the user gives a partial or uncertain country name —
        e.g. 'stan', 'united', 'new' — and expects multiple possible matches.
        Returns up to 25 matching country records, each with 20 fields
        including population, GDP, literacy rate, and region.
        """
        return search_countries(name_fragment)

    @mcp.tool()
    def lookup_country(country: str) -> CountryRecord | None:
        """Retrieve the full record for one country by its exact official name.

        Use this tool when the user names a specific country and wants its details —
        e.g. 'France', 'Brazil', 'Japan'. Requires the exact country name as stored
        in the database. Returns one record with 20 fields (population, GDP,
        literacy, region, etc.) or null if no match is found.
        If uncertain about the exact spelling, use search_countries_by_name first.
        """
        return get_country(country)
```

> **Note:** The `search_countries_by_name` function above accepts a `region` parameter in its signature but doesn't use it in the body yet — the underlying `search_countries()` query would need a `WHERE` clause for region filtering. The parameter is shown here to demonstrate how `Literal` types surface as enum constraints in the JSON schema. Wiring it into the SQL is left as an exercise.



---

> **Coming up next:** we plug this label-rich server into a real LLM client and watch it pick tools *live* — same question, good descriptions vs. weak ones, and which tool it grabs. That's the payoff for everything we just inspected.
>
> And in a future part: we graduate from type hints to **Pydantic `Field()`** — parameter-level descriptions, `min_length`, `pattern`, `examples`, and custom validators. The bouncer gets a clipboard.
