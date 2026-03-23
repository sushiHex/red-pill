---
name: oracle
description: "Multi-tier research orchestrator. Local session decomposes -> N*10 Smiths (Haiku) scout -> Anderson (Sonnet) synthesizes. Python enforces isolation — Anderson never sees raw Smith data."
argument-hint: "[chains] <research question>"
user-invocable: true
---

# Oracle v4.2 — SDK Execution

Run the oracle_sdk.py script with the user's research question.

## Parse arguments

`$ARGUMENTS` uses this format: `[N] <question>`

If the first word is a number (e.g., `4`), use it as the chain count and the rest is the question.
If no number, default to 1 chain and the entire string is the question.

Examples:
- `/oracle what are AI agents` -> chains=1, question="what are AI agents"
- `/oracle 4 what are AI agents` -> chains=4, question="what are AI agents"
- `/oracle 8 compare LLM hosting` -> chains=8, question="compare LLM hosting"

## Build Smith prompts

You ARE the Architect. Using your full conversation context, decompose the question into exactly `chains * 10` focused sub-prompts. Each Smith is a Haiku agent with WebSearch, WebFetch, Read, Grep, Glob, and GitHub MCP tools.

Generate a JSON array — chain/id/suffix are auto-assigned by Python:
```json
[
  {"dimension": "short label", "prompt": "the focused sub-prompt text"},
  {"dimension": "another label", "prompt": "another sub-prompt text"}
]
```

Guidelines:
- Each prompt targets ONE narrow question a Haiku agent can fully answer in ~1500 tokens. If you find yourself listing multiple sub-topics in one prompt, split them into separate Smiths.
- BAD: "Research all Obsidian MCP servers, their tools, and integration patterns"
- GOOD: "Find the top 3 Obsidian MCP servers on GitHub. For each: name, repo URL, star count, what tools it exposes."
- Each prompt should be under 150 words. Confidence/reporting instructions are auto-appended — don't include them.
- For multi-chain: generate `chains * 10` entries. Python auto-splits into chains of 10.
- Use your conversation context and judgement to craft the best possible decomposition.

## Execution

Write the JSON prompts to a temporary file, then pipe it into the script. Do NOT use heredocs — they break on Windows with JSON containing quotes.

Find `oracle_sdk.py` in the same directory as this SKILL.md file, then run:

```bash
python <path-to-oracle_sdk.py> --verbose < oracle_prompts.json
```

Status lines stream to stderr in real-time. The report prints to stdout.

## After completion

1. Present the findings and execution metrics to the user.
2. Save the report to the Mainframe via `/mainframe save`, targeting the `oracle/` folder with filename `<YYYY-MM-DD>-<topic-slug>.md`.
