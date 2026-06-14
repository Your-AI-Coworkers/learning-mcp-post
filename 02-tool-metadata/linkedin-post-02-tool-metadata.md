𝗬𝗼𝘂𝗿 𝗔𝗜 𝗱𝗶𝗱𝗻'𝘁 𝗽𝗶𝗰𝗸 𝘁𝗵𝗲 𝘄𝗿𝗼𝗻𝗴 𝘁𝗼𝗼𝗹 𝗯𝗲𝗰𝗮𝘂𝘀𝗲 𝗶𝘁'𝘀 𝘀𝘁𝘂𝗽𝗶𝗱. 𝗜𝘁 𝗽𝗶𝗰𝗸𝗲𝗱 𝘁𝗵𝗲 𝘄𝗿𝗼𝗻𝗴 𝘁𝗼𝗼𝗹 𝗯𝗲𝗰𝗮𝘂𝘀𝗲 𝘆𝗼𝘂 𝗶𝗻𝘁𝗿𝗼𝗱𝘂𝗰𝗲𝗱 𝘁𝗵𝗲𝗺 𝗯𝗮𝗱𝗹𝘆.

Week two of my learning-mcp series. Three MCP tools. Clean SQL. Tests pass. Ship it at 4:55 PM on a Friday.

Then the LLM calls the wrong one. Every. Single. Time.

The model never sees your Python. It reads a JSON description of your tools — name, description, input schema, output schema — and decides from that alone. Like hiring someone based entirely on their LinkedIn headline. The irony of saying this here is not lost on me.

𝗙𝗼𝘂𝗿 𝗺𝗲𝘁𝗮𝗱𝗮𝘁𝗮 𝗳𝗶𝘅𝗲𝘀. 𝗭𝗲𝗿𝗼 𝗹𝗶𝗻𝗲𝘀 𝗼𝗳 𝗶𝗺𝗽𝗹𝗲𝗺𝗲𝗻𝘁𝗮𝘁𝗶𝗼𝗻 𝗰𝗵𝗮𝗻𝗴𝗲𝗱:

▸ 𝗡𝗮𝗺𝗲 — renamed `get_country_tool` to `lookup_country` and `search_countries_tool` to `search_countries_by_name`. With 15 tools in a context window, "get" and "search" are the same word wearing different hats.

▸ 𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻 — one-sentence mumbling ("Search countries by partial name match") became a three-part contract: what I do, when to pick me, what I give back. Added 𝘁𝗼𝗼𝗹 𝗰𝗵𝗼𝗿𝗲𝗼𝗴𝗿𝗮𝗽𝗵𝘆 — "If unsure of spelling, use search_countries_by_name first." 𝗗𝗲𝗰𝗶𝘀𝗶𝗼𝗻 𝗹𝗼𝗴𝗶𝗰 𝗹𝗶𝘃𝗶𝗻𝗴 𝗲𝗻𝘁𝗶𝗿𝗲𝗹𝘆 𝗶𝗻 𝗮 𝗱𝗼𝗰𝘀𝘁𝗿𝗶𝗻𝗴. 𝗡𝗼 𝗼𝗿𝗰𝗵𝗲𝘀𝘁𝗿𝗮𝘁𝗶𝗼𝗻 𝗳𝗿𝗮𝗺𝗲𝘄𝗼𝗿𝗸.

▸ 𝗜𝗻𝗽𝘂𝘁 𝗦𝗰𝗵𝗲𝗺𝗮 — bare `"type": "string"` became a `Literal` enum of 11 valid regions. Model can no longer hallucinate "Middle Earth" as a valid region. Bouncer got a guest list.

▸ 𝗢𝘂𝘁𝗽𝘂𝘁 𝗦𝗰𝗵𝗲𝗺𝗮 — `additionalProperties: {"type": "string"}` (translation: "good luck") became a `TypedDict` naming all 20 fields. Model knows what keys to expect before the response arrives.

The shift that matters: 𝗺𝗲𝘁𝗮𝗱𝗮𝘁𝗮 𝗶𝘀 𝗻𝗼𝘁 𝗱𝗼𝗰𝘂𝗺𝗲𝗻𝘁𝗮𝘁𝗶𝗼𝗻 𝘆𝗼𝘂 𝘄𝗿𝗶𝘁𝗲 𝗮𝗳𝘁𝗲𝗿 𝘁𝗵𝗲 𝗿𝗲𝗮𝗹 𝘄𝗼𝗿𝗸. It 𝗶𝘀 𝘁𝗵𝗲 𝗿𝗲𝗮𝗹 𝘄𝗼𝗿𝗸. It's 𝘁𝗵𝗲 𝗼𝗻𝗹𝘆 𝗶𝗻𝘁𝗲𝗿𝗳𝗮𝗰𝗲 𝗯𝗲𝘁𝘄𝗲𝗲𝗻 𝘆𝗼𝘂𝗿 𝘁𝗼𝗼𝗹 𝗮𝗻𝗱 𝘁𝗵𝗲 𝗺𝗼𝗱𝗲𝗹'𝘀 𝗱𝗲𝗰𝗶𝘀𝗶𝗼𝗻-𝗺𝗮𝗸𝗶𝗻𝗴. Get it right — model behaves. Get it sloppy — your boss says "see, I told you the AI thing wouldn't work."

𝗦𝗮𝗺𝗲 𝘁𝗵𝗿𝗲𝗲 𝗳𝘂𝗻𝗰𝘁𝗶𝗼𝗻𝘀. 𝗦𝗮𝗺𝗲 𝗦𝗤𝗟. 𝗦𝗮𝗺𝗲 𝗿𝗲𝘀𝘂𝗹𝘁𝘀. 𝗗𝗶𝗳𝗳𝗲𝗿𝗲𝗻𝘁 𝗹𝗮𝗯𝗲𝗹𝘀. 𝗖𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗹𝘆 𝗱𝗶𝗳𝗳𝗲𝗿𝗲𝗻𝘁 𝗯𝗲𝗵𝗮𝘃𝗶𝗼𝘂𝗿.

If you're building MCP tools and skipping metadata — you're writing code the model will never read, and skipping the part it actually does.

https://github.com/Your-AI-Coworkers/learning-mcp-post/tree/main/02-tool-metadata

#MCP #ModelContextProtocol #FastMCP #Python #AIEngineering #AppliedAI #AIInPractice #LearningInPublic #ToolMetadata #AEC
