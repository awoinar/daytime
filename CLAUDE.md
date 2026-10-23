# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Sunrise/sunset and day-length info for București, Berlin and Freiburg — exposed both as a CLI (București only) and as a Streamlit app with charts and a city picker. All user-facing strings are in **Romanian**; preserve that when editing.

## Commands

Project uses `uv` (see `uv.lock`, `.python-version`).

```bash
uv sync                         # install deps into .venv
uv run daytime.py               # CLI for today
uv run daytime.py 2026-12-25    # CLI for a specific date (YYYY-MM-DD)
uv run streamlit run app.py     # launch the Streamlit UI
```

There is no test suite or linter config.

## Container

`Dockerfile` builds the app image: Python 3.12, dependencies from `uv.lock`, Streamlit on port 8501, `TZ=Europe/Bucharest` so the CLI's `date.today()` is the Bucharest date (the app uses the chosen city's date instead). `.dockerignore` is an allowlist: a new source file must be added both there and to the `COPY` line, or the image won't contain it.

On every push to `main`, `.github/workflows/build.yml` builds the image for `linux/arm64` and pushes it to `ghcr.io/awoinar/daytime`, tagged `latest` and `sha-<short commit>`. Its `deploy` job then logs into the server `bebop` over SSH, which runs `/opt/daytime/deploy.sh` (pull, restart, prune), and fails unless the server reports the pushed commit. So a push to `main` goes live within about a minute. The key, secrets and rollback are described in the `hetzner` repo (`daytime.md`).

## Architecture

- `daytime.py` — core logic plus CLI. `calculeaza(data: date, oras: LocationInfo) -> InfoZi` is the **pure compute function** (no I/O); both the CLI's `info_zi()` printer and the Streamlit app consume it. The cities live here in `ORASE`, a dict from an ASCII key (`bucuresti`, `berlin`, `freiburg`) to `LocationInfo`; `ORAS_IMPLICIT` is the default. To add a city, add an entry there; the app's picker follows the dict order.
- `app.py` — Streamlit front-end. Renders a city picker, metrics, an annual day-length curve with the selected date marked, and a 24h day/night strip (Altair charts, pandas frames). The annual curve is wrapped in `@st.cache_data` keyed on city key and year — 365 `astral` calls each, fast but worth caching.
- The app remembers the last city in a cookie `oras` holding the city's key, kept for a year. It is read once per page load from `st.context.cookies`, so a city picked now shows up on the next visit. It is written by a `<script>` in `st.html(..., unsafe_allow_javascript=True)` at the bottom of the page. A missing or unknown value falls back to `ORAS_IMPLICIT`. Only ever put a key of `ORASE` into that script, never the raw cookie text.
- `main.py` — unrelated `print("Hello from daytime!")` stub left over from `uv init`. Not the entry point.

## Conventions

- Identifiers are in Romanian (`oras`, `rasarit`, `apus`, `durata`, `calculeaza`) to match user-facing strings. Keep that style in new code.
- Keep `calculeaza()` pure (no prints, no Streamlit calls). The CLI and UI are both thin layers on top — anything that should appear in both belongs in the dataclass.
- Signed deltas: compute `int((a - b).total_seconds())` then split sign from `abs()` before formatting. The earlier `dif_sec // 60` + `dif_sec % 60` pattern produced wrong output for negative deltas; don't reintroduce it.
