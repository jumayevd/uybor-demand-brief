# Tashkent Housing Demand Brief — daily refresh automation

Every morning this repo recomputes the aggregate object `D` from the Uybor
listing-day panel in Supabase, injects it into
`tashkent_demand_brief.template.html`, and commits the refreshed
`tashkent_demand_brief.html` (+ `index.html` copy) so GitHub Pages serves the
updated brief. The charts are Chart.js reading `D` client-side — there is no
image rendering step anywhere, by design.

## How it works

```
Supabase (uybor_listings_v2)          tashkent_demand_brief.template.html
            │                                        │
            ▼                                        │
   refresh_brief.py  ── build_D() ── validate_D() ── inject D + timestamp
            │
            ▼
   tashkent_demand_brief.html  (and index.html)  →  GitHub Pages
```

`refresh_brief.py` is deliberately fail-loud: if the DB is unreachable, the
query returns no rows, any of the 13 required `D` keys would be empty, the
district cut is not exactly the canonical 12, the funnel is not monotone,
any number is NaN/Inf, or the newest snapshot date is older than the one in
the currently published brief, it exits non-zero **without touching the
existing output file** (writes are atomic: temp file + rename).

Metric definitions live at the top of `refresh_brief.py`. They were
calibrated field-by-field against the published brief: on the reference CSV
every shared `daily` entry reproduces exactly, and the remaining deltas are
attributable to the CSV missing the final (Jul 13) snapshot.

## Scheduling — GitHub Actions is primary

`.github/workflows/daily-brief.yml` runs at **02:00 UTC (07:00 Tashkent)**
daily, plus on manual `workflow_dispatch`.

**Timing:** the scraper stamps each day's snapshot at **20:00 UTC** (01:00
Tashkent, next calendar day locally). The 02:00 UTC refresh therefore runs
~6 h after the newest snapshot lands. If the scrape schedule ever moves
later than ~01:30 UTC, shift the cron accordingly.

### One-time setup (copy-paste)

```bash
# 1. create the repo and push (from the repo root)
git init -b main && git add -A && git commit -m "initial import"
gh repo create uybor-demand-brief --public --source . --push

# 2. store the connection string as an Actions secret (never commit it)
gh secret set SUPABASE_DB_URL --body "postgresql://USER:PASSWORD@HOST:PORT/postgres"

# 3. (optional) non-default table name
gh variable set UYBOR_TABLE --body "uybor_listings_v2"

# 4. enable GitHub Pages: Settings → Pages → Source: "Deploy from a branch",
#    Branch: main, folder: / (root). CLI equivalent:
gh api repos/{owner}/{repo}/pages -X POST \
  -f "source[branch]=main" -f "source[path]=/"

# 5. smoke-test the pipeline
gh workflow run daily-brief && gh run watch
```

The published URL is `https://<owner>.github.io/uybor-demand-brief/`
(`index.html` is a copy of the brief; the canonical file URL is
`.../tashkent_demand_brief.html`). Each run stamps
`<!-- generated: <UTC timestamp> UTC -->` before `</body>` — view-source to
confirm freshness.

Connection note: use the Supabase **session pooler / direct** connection
(port 5432) or the transaction pooler (6543) — both work; the script runs a
single read-only SELECT of the needed columns.

## Scheduling — cron alternative

`run_daily.sh` does the same refresh on any box (e.g. the scraper host):

```bash
export SUPABASE_DB_URL="postgresql://..."   # or put it in ./.env (chmod 600)
./run_daily.sh
# crontab: 10 7 * * *  (07:10 Tashkent) — after the 01:00 local scrape
```

Set `PUBLISH_DIR=/var/www/brief` to copy the refreshed HTML into a webroot.

## Local / offline usage

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
python refresh_brief.py \
  --csv uybor_listings_v2_rows.csv \
  --template tashkent_demand_brief.template.html \
  --out /tmp/out.html
```

`--csv` and the DB path produce identical `D` shapes. On success the script
prints a one-line summary (listings, days, latest date, top-10% share,
median vpd).

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

The suite validates the 13-key contract, the canonical 12-district cut, the
Cyrillic `by_newbuild` keys, funnel monotonicity, flow clipping /
cumulative-max semantics, quintile shape, and an inject→re-parse round-trip.

## Operational notes

* **Never overwrite good output with bad** — validation runs before any
  write; failures leave the last good HTML in place and exit non-zero, so
  the Pages site simply keeps yesterday's brief.
* **Secrets** only via `SUPABASE_DB_URL` (Actions secret / env var). The
  script never prints the URL.
* **History**: currently only the latest brief is kept (git history retains
  every generated version anyway). If you want dated snapshots
  (`briefs/2026-07-20.html`), add a `cp` line in the workflow.
* The hero copy in the template (listing counts, date window, thesis
  numbers) is static prose and is NOT rewritten by the pipeline — per spec,
  only `D` changes. Expect the prose to drift from the charts as data grows;
  updating it is a future task.
* `overall.ppm2_mean` intentionally contains the *median* $/m² — the
  published fixture does the same and nothing reads the field; kept for
  schema compatibility.
