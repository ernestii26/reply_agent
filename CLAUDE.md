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
```

Required environment variables (copy `.env.example` → `.env`):
- `EMAIL`, `PASSWORD` — forum credentials
- `GEMINI_API_KEY` or `GEMINI_API_KEYS` — supports multi-key rotation (JSON array or comma-separated)
- `SERPER_API_KEY` — external search (optional; disables RAG if missing)

For testing without posting, set `BROWSER_CONFIG["dry_run"] = True` in [config/settings.py](config/settings.py).

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

1. Login via Playwright
2. Load processed post IDs from SQLite (prevents duplicates)
3. Patrol posts: keyword search (`mode="keyword"`) or board browse (`mode="board"`)
4. For each post: check SQLite → check already-replied in DOM → AI decision → RAG enrichment → generate reply → submit → save to DB
5. Stop when `min_replies_per_run` target is met

### API Key Rotation

Both `AIHandler` and `SearchHandler` implement the same pattern: test keys on init, use the first working one, immediately switch on failure, `sys.exit(1)` if all keys exhausted. AI decision failures fall back to keyword matching (question marks, 請問, etc.) rather than failing.

### Key Configuration (config/settings.py)

| Setting | Default | Notes |
|---|---|---|
| `BROWSER_CONFIG["dry_run"]` | `False` | Set `True` to disable actual posting |
| `BROWSER_CONFIG["min_replies_per_run"]` | `8` | Stop after this many replies |
| `BROWSER_CONFIG["headless"]` | auto | `True` when `CI=true` (GitHub Actions sets this automatically), `False` locally |
| `AI_CONFIG["reply_min_length"]` | `30` | Characters |
| `AI_CONFIG["reply_max_length"]` | `200` | Characters |
| `AGENT_PATROL_CONFIG["mode"]` | `"keyword"` | `"keyword"` or `"board"` |
| `AGENT_PATROL_CONFIG["target_keywords"]` | `["資工", "電機", ...]` | Keywords to search |
| `SEARCH_CONFIG["enable_external_search"]` | `True` | Toggle Serper RAG |
| `SELECTORS` | Dict | CSS selectors — update if forum layout changes |

### SQLite Schema

```sql
replied_posts (post_id TEXT PK, inserted_at INTEGER, source TEXT)
replies_log   (id PK, post_id, title, reply, timestamp, reply_hash)
-- Unique index on (post_id, reply_hash) prevents duplicate replies
```

### Google Drive Sync

`utils/drive_sync.py` handles DB and screenshot persistence across GitHub Actions runs (stateless runners). Run manually:

```bash
python -m utils.drive_sync download   # before main.py — fetches storage.db
python -m utils.drive_sync upload     # after main.py  — pushes storage.db, screenshots/M/D/
```

Screenshots are stored under a date-based subfolder (Taiwan time, e.g. `3/27`) inside the screenshots folder.

To generate a refresh token (one-time):
```bash
python get_refresh_token.py
```

### Deployment

Automated via GitHub Actions (`.github/workflows/run.yml`): runs daily at 09:00 Taiwan time (01:00 UTC).

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
