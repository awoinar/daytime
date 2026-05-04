# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Sunrise/sunset and day-length info for Bucharest — exposed both as a CLI and as a Streamlit app with charts. All user-facing strings are in **Romanian**; preserve that when editing.

## Commands

Project uses `uv` (see `uv.lock`, `.python-version`).

```bash
uv sync                         # install deps into .venv
uv run daytime.py               # CLI for today
uv run daytime.py 2026-12-25    # CLI for a specific date (YYYY-MM-DD)
uv run streamlit run app.py     # launch the Streamlit UI
```

There is no test suite, linter config, or build step.

## Architecture

- `daytime.py` — core logic plus CLI. `calculeaza(data: date) -> InfoZi` is the **pure compute function** (no I/O); both the CLI's `info_zi()` printer and the Streamlit app consume it. The hardcoded `LocationInfo` for Bucharest lives here.
- `app.py` — Streamlit front-end. Renders metrics, an annual day-length curve with the selected date marked, and a 24h day/night strip (Altair charts, pandas frames). The annual curve is wrapped in `@st.cache_data` keyed on year — 365 `astral` calls per year, fast but worth caching.
- `main.py` — unrelated `print("Hello from daytime!")` stub left over from `uv init`. Not the entry point.

## Conventions

- Identifiers are in Romanian (`oras`, `rasarit`, `apus`, `durata`, `calculeaza`) to match user-facing strings. Keep that style in new code.
- Keep `calculeaza()` pure (no prints, no Streamlit calls). The CLI and UI are both thin layers on top — anything that should appear in both belongs in the dataclass.
- Signed deltas: compute `int((a - b).total_seconds())` then split sign from `abs()` before formatting. The earlier `dif_sec // 60` + `dif_sec % 60` pattern produced wrong output for negative deltas; don't reintroduce it.
