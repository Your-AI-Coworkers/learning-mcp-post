

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

> **[LAB is next](tutorial-part2-lab.md)**