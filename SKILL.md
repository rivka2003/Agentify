---
name: Agentify
description: Turn any website into an LLM-callable API. Phase 1 ("map") visits a site, proposes tool functions, and records deterministic Playwright recipes into recipes/<slug>.tools.json. Phase 2 ("call" or "run-mapped") replays a recipe directly or lets the LLM pick a tool from natural language — the page itself is never sent to the model. Use when the user wants to scrape, automate, or expose a website as tools.
argument-hint: "[map|call|run-mapped] [...args]"
allowed-tools: Bash, Read
---

# Agentify

Self-contained skill that bundles the `agentify` CLI, its Python venv, and the Playwright Chromium browser. Nothing installs at invocation time — just run the bundled interpreter.

> **Skill location (`$SKILL_DIR`).** This same skill runs in both Claude Code
> and Codex; only the install folder differs. Every command below uses
> `$SKILL_DIR` for that folder — set it to whichever applies to your tool:
>
> ```bash
> export SKILL_DIR=~/.claude/skills/Agentify   # Claude Code
> export SKILL_DIR=~/.agents/skills/Agentify   # Codex
> ```

## Run with the bundled venv (never `pip install` again)

The skill ships everything pre-installed at `$SKILL_DIR/venv/` and the source at `$SKILL_DIR/source/`. Always invoke through the venv's Python so dependencies resolve correctly:

```bash
"$SKILL_DIR/venv/bin/python" -m agentify.cli --help
```

The CLI's `_load_env` walks up from the package and finds `source/.env` automatically, so `OPENAI_API_KEY` is already wired up.

## Phase 1 — map a site (one-shot per site)

Crawls the landing page, asks the LLM to propose tool functions, prompts you to accept/reject each one, then drives the site to record a deterministic recipe per tool. Output is written to `$SKILL_DIR/source/recipes/<name>.tools.json`.

```bash
"$SKILL_DIR/venv/bin/python" -m agentify.cli map \
  --url https://news.ycombinator.com --name hackernews
```

Flags:
- `--auto-approve` — skip the interactive accept/reject step
- `--no-headless` — show the browser while recording
- `--model gpt-4o-mini` — override `AGENTIFY_MODEL` from .env

### Multi-step flows (any site, no per-site code)

`map` records arbitrary linear multi-step flows — fill several fields, pick
autocomplete suggestions, submit, read the result page — using four
site-agnostic mechanisms:

1. **Realistic example inputs.** The proposer supplies a real value per field
   (`"TLV"`, not `"xxx"`), so dynamic widgets (typeaheads, live search) respond
   while recording. Without this, dropdowns never open and the flow can't be
   captured.
2. **Autocomplete normalization.** Any `type into a combobox → click a
   suggestion` is rewritten to "type `{{param}}` → wait for an option → click
   the **first** option," which is input-independent and replays for any value.
3. **Auto result-extraction.** Whatever page the flow lands on, the mapper
   generates a `js_extract` so the tool returns data.
4. **Self-verifying record→replay.** After the LLM records the steps, the
   mapper deterministically replays the recipe with the example values to prove
   it works; on failure it re-records once with the failure fed back as a hint.
   The console prints a `replay check passed/failed` line per tool.

Recording costs LLM calls once, at map time. Replay (`call`) is pure Playwright
with **zero** LLM calls — typically a few seconds for a multi-step flow, versus
an LLM round-trip per step in a general agentic browser.

## Phase 2a — call a single tool directly (no LLM)

Deterministic replay of a recorded recipe with explicit JSON args.

```bash
"$SKILL_DIR/venv/bin/python" -m agentify.cli call \
  --site hackernews --tool get_top_stories --args '{"n": 5}'
```

## Phase 2b — natural-language run (LLM picks the tool, never sees the page)

```bash
"$SKILL_DIR/venv/bin/python" -m agentify.cli run-mapped \
  --site hackernews \
  --task "Give me the top 3 stories right now"
```

## Where things live

| Path | Purpose |
|------|---------|
| `$SKILL_DIR/venv/` | Python venv with playwright, typer, openai, rich, python-dotenv |
| `$SKILL_DIR/source/` | Editable install of the `agentify` package |
| `$SKILL_DIR/source/recipes/` | Generated `<slug>.tools.json` registries |
| `$SKILL_DIR/source/.env` | `OPENAI_API_KEY`, `AGENTIFY_MODEL` |
| `~/Library/Caches/ms-playwright/chromium-*` | Bundled Chromium browser (managed by Playwright) |

## Recipe shape (for reference)

Each tool is `{name, description, parameters: JSON-Schema, steps: [...]}`. Step ops: `goto`, `click`, `type`, `select`, `press_enter`, `press`, `scroll`, `wait`, `extract`, `js_extract`, `verify`. Selectors try role+name → CSS → text in order; a target of `{"role": "option"}` resolves to the first match, which is how autocomplete suggestions are selected parameter-independently. `press` sends a key (e.g. `{"op": "press", "key": "Enter"}`) to a target, or to whatever is focused if no target is given.

## Updating the skill

The source under `source/` is an editable install — edit files there and changes apply on the next invocation. If `pyproject.toml` gains a new dependency, re-run:

```bash
"$SKILL_DIR/venv/bin/python" -m pip install -e "$SKILL_DIR/source"
```

If Playwright is upgraded, reinstall the browser:

```bash
"$SKILL_DIR/venv/bin/python" -m playwright install chromium
```

## Full reference

See `$SKILL_DIR/README.md` for the design rationale, known limitations (no session persistence between `call` invocations, no iteration op, shallow crawler), and extension paths.
