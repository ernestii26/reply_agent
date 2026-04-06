# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

An automated forum reply bot for Taiwan's NTU college admission forum (pei.com.tw). It patrols the forum, identifies relevant questions, enriches context via external search (Serper/RAG), and generates replies using Google Gemini. Written in Traditional Chinese.

## Running the Agent

```bash
# Setup (one-time)
pip install -r requirements.txt
playwright install chromium

# Run
python main.py

# Or via shell script
bash run_main.sh

# Google Drive sync (used by GitHub Actions)
python -m utils.drive_sync download   # fetch storage.db before run
python -m utils.drive_sync upload     # push storage.db + screenshots after run

# Generate Google OAuth refresh token (one-time setup)
python get_refresh_token.py
```

Required environment variables (copy `.env.example` → `.env`):
- `EMAIL`, `PASSWORD` — forum credentials
- `GEMINI_API_KEY` or `GEMINI_API_KEYS` — supports multi-key rotation (JSON array or comma-separated)
- `SERPER_API_KEY` — external search (optional; disables RAG if missing)

For testing without posting, set `BROWSER_CONFIG["dry_run"] = True` in [config/settings.py](config/settings.py).

There are no automated tests in this repository.

## Architecture

```
main.py                     ← Orchestrator; runs the full patrol loop
config/settings.py          ← All configuration (timeouts, selectors, AI params, URLs)
config/prompts/             ← AI prompt templates (decision, reply, keyword, search strategy)
core/ai_handler.py          ← Gemini API wrapper; multi-key rotation; decision + reply generation
core/browser_handler.py     ← Playwright automation (login, navigate, extract posts, submit reply)
core/search_handler.py      ← Serper API RAG; keyword extraction; context enrichment
utils/sqlite_storage.py     ← SQLite persistence (processed post IDs + reply log)
utils/logger.py             ← Colored console + file logging
logs/                       ← Runtime outputs: agent.log, storage.db, screenshots/
```

### Processing Pipeline

`main.py:run()` orchestrates everything:

1. Initialize handlers (logger, storage, AI, search, browser)
2. `storage.load()` — pulls all processed post IDs into an in-memory set for fast dedup
3. Patrol posts via one or both modes (runs sequentially, stops early when `min_replies_per_run` met):
   - `"keyword"` mode: `search_feed(kw)` → `get_posts()` for each keyword
   - `"board"` mode: `navigate_to_board()` → `scroll_load_more()` loop with `seen_post_ids` set to track new posts across scrolls
4. For each post batch: extract all post metadata (ID/title/URL) upfront before navigating — this avoids Playwright locator staleness
5. Per post: `storage.contains()` → DOM `check_if_already_replied()` → `ai.should_reply()` → `search.get_enriched_context()` → `ai.generate_reply()` → `browser.submit_reply()` → `storage.save_reply()` + `storage.save()`

### Fallback / Degradation Architecture

**AI decisions** (`ai_handler.py`) have 3 layers:
1. Gemini API generation
2. Immediate key rotation on failure — switches to next key, retries once
3. `_basic_should_reply()` — hardcoded keyword fallback (question marks, `請問`, etc.) if all AI keys fail; only `should_reply()` degrades this way, `generate_reply()` calls `sys.exit(1)` if all keys exhausted

**Search / RAG** (`search_handler.py`) never hard-stops:
1. AI generates optimal Serper query (returns JSON; regex-extracted from raw Gemini response)
2. Falls back to `extract_keywords()` if strategy generation fails
3. Returns empty context string on any Serper failure — main loop continues without enrichment

**Submit button** (`browser_handler.py`) tries 3 CSS selector strategies in sequence before giving up.

### Configuration (config/settings.py)

`settings.py` is the single source of truth — it loads `.env`, reads all prompt files via `_load_prompt()`, and exports structured dicts consumed by every other module.

| Setting | Default | Notes |
|---|---|---|
| `BROWSER_CONFIG["dry_run"]` | `False` | Set `True` to disable actual posting |
| `BROWSER_CONFIG["min_replies_per_run"]` | `8` | Stop after this many replies |
| `BROWSER_CONFIG["headless"]` | auto | `True` when `CI=true` env var is set (GitHub Actions), `False` locally |
| `AI_CONFIG["reply_min_length"]` | `30` | Characters |
| `AI_CONFIG["reply_max_length"]` | `200` | Characters |
| `AGENT_PATROL_CONFIG["mode"]` | `"keyword"` | `"keyword"` or `"board"` |
| `SEARCH_CONFIG["enable_external_search"]` | `True` | Toggle Serper RAG |
| `SELECTORS` | Dict | CSS selectors — update here if forum layout changes |
| `WAIT_TIMES` | Dict (ms) | All sleep durations; `"after_submit_screenshot"` is intentionally long (10s) for page render |

### Prompt Files (config/prompts/)

- **`decision_prompt.txt`** — expects a plain `YES`/`NO` response
- **`reply_prompt.txt`** — most complex; enforces NTU CS student persona, extensive list of prohibited words/patterns, no Markdown, no default greetings; explicitly references 1111.com.tw
- **`keyword_extract_prompt.txt`** — expects space-separated keywords
- **`external_search_strategy_prompt.txt`** — requires pure JSON output (`{"query": "..."}`) with no Markdown wrappers; injects current year

`ai_handler.py` also runs `_remove_markdown()` (regex-based) to strip any formatting Gemini adds despite instructions.

### SQLite Schema

```sql
replied_posts (post_id TEXT PK, inserted_at INTEGER, source TEXT)
replies_log   (id PK, post_id, title, reply, timestamp, reply_hash)
-- Unique index on (post_id, reply_hash) prevents duplicate replies
```

Storage uses WAL mode + `SYNCHRONOUS=NORMAL`. `storage.load()` builds an in-memory set; `storage.contains()` is always an in-memory lookup. Both tables use `INSERT OR IGNORE` so the agent is safe to re-run on already-processed posts.

### Google Drive Sync

`utils/drive_sync.py` persists state across stateless GitHub Actions runners. Screenshots upload under Taiwan-time date subfolders (e.g. `3/27`). `_upload_file()` checks for existing files and updates vs. creates.

### Deployment

Automated via GitHub Actions (`.github/workflows/run.yml`): runs daily at 06:23 Taiwan time.

Required GitHub Secrets:

| Secret | Purpose |
|---|---|
| `EMAIL`, `PASSWORD` | Forum login |
| `GEMINI_API_KEYS` | AI replies |
| `SERPER_API_KEY` | External search RAG |
| `GDRIVE_CLIENT_ID` | OAuth client ID |
| `GDRIVE_CLIENT_SECRET` | OAuth client secret |
| `GDRIVE_REFRESH_TOKEN` | OAuth refresh token (from `get_refresh_token.py`) |
| `GDRIVE_DB_FOLDER_ID` | Drive folder for `storage.db` |
| `GDRIVE_SCREENSHOTS_FOLDER_ID` | Drive folder for screenshots |

## Debugging

- `logs/agent.log` — detailed execution log
- `logs/screenshots/` — screenshot after each submitted reply
- `logs/storage.db` — query with `sqlite3` to inspect processed posts and reply history
