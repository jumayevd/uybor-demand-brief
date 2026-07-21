# Tashkent Housing Demand Brief — daily refresh automation

Every morning this repo recomputes the aggregate object `D` from the Uybor
listing-day panel in Supabase, injects it into
`tashkent_demand_brief.template.html`, commits the refreshed
`tashkent_demand_brief.html` (+ `index.html` copy) so GitHub Pages serves the
updated brief, and renders each chart to a dated PNG folder
(`briefs/YYYY-MM-DD/`). The live charts are Chart.js reading `D` client-side;
the PNGs are produced by loading that same page in headless Chromium and
exporting each `<canvas>`.

## Scope: apartments only

Every figure in the brief is computed on **apartment (`Квартира`) listings
only** — houses, commercial, and land are excluded up front in `build_D`. The
two former cross-category charts (exit rate by type, demand by type) were
removed since with one category they carry no information.

## How it works

```
Supabase (uybor_listings_v2)          tashkent_demand_brief.template.html
            │  (apartments only)                      │
            ▼                                        │
   refresh_brief.py  ── build_D() ── validate_D() ── inject D + timestamp
            │                                          │
            ▼                                          ▼
   tashkent_demand_brief.html (+ index.html) ──► GitHub Pages
            │
            ▼
   render_charts.py ── headless Chromium ── briefs/YYYY-MM-DD/*.png
```

`refresh_brief.py` is deliberately fail-loud: if the DB is unreachable, the
query returns no rows, any of the 13 required `D` keys would be empty, the
district cut is not exactly the canonical 12, the funnel is not monotone,
any number is NaN/Inf, or the newest snapshot date is older than the one in
the currently published brief, it exits non-zero **without touching the
existing output file** (writes are atomic: temp file + rename).

Metric definitions live at the top of `refresh_brief.py`. They were
calibrated field-by-field against the originally published (all-category)
brief before the apartments-only scope was applied; the definitions are
unchanged, only the input population is now filtered to `Квартира`.

## Scheduling — precise 07:00 Tashkent via cron-job.org

GitHub's built-in `schedule` is **best-effort and lags** the target minute
(often 5–60 min at popular times), so it cannot hit 07:00 reliably. The precise
trigger is therefore external: a free **cron-job.org** job calls GitHub's
`workflow_dispatch` API at exactly 07:00 Asia/Tashkent; API dispatches start
immediately. GitHub's own `schedule` is kept only as a fallback (08:00
Tashkent) and the workflow's *gate* step makes it skip when the day's brief
already exists — so no duplicate commits.

### One-time cron-job.org setup

1. **Create a fine-grained GitHub token** (github.com → Settings → Developer
   settings → Fine-grained tokens → Generate):
   - Resource owner: your account; Repository access: **Only**
     `uybor-demand-brief`.
   - Permissions → Repository → **Actions: Read and write**.
   - Copy the token (starts `github_pat_…`).
2. **Create the cron job** at <https://cron-job.org> (free account):
   - URL:
     `https://api.github.com/repos/jumayevd/uybor-demand-brief/actions/workflows/daily-brief.yml/dispatches`
   - Request method: **POST**
   - Schedule: **07:00**, every day, timezone **Asia/Tashkent** (cron-job.org
     lets you pick the timezone — no UTC math needed).
   - Headers:
     - `Accept: application/vnd.github+json`
     - `Authorization: Bearer github_pat_…`  (your token)
     - `Content-Type: application/json`
   - Request body: `{"ref":"main"}`
   - Enable "notify on failure" so you hear about it if a run ever fails.
3. Save. A successful dispatch returns HTTP **204** (cron-job.org shows it
   green). The workflow appears in the repo's Actions tab within seconds.

The token is stored in cron-job.org, never in this repo. If you rotate or
revoke it, update the header there. Scope is minimal (one repo, Actions only),
so a leak can at most trigger this workflow.

**Data timing:** the scraper stamps each day's snapshot at **20:00 UTC** (01:00
Tashkent). The 07:00 Tashkent refresh runs ~6 h later, so the freshest snapshot
is always included.

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

## Chart pictures

`render_charts.py` loads a generated brief in headless Chromium and writes one
PNG per chart into a dated folder. In CI this runs automatically after each
refresh; the folders (`briefs/2026-07-20/…`) are committed alongside the HTML,
so the repo becomes a growing dated image archive (~11 PNGs, ~0.3 MB/day).

Run it locally:

```bash
pip install -r requirements-render.txt
python -m playwright install chromium          # one-time browser download
python render_charts.py \
  --html tashkent_demand_brief.html \
  --outdir briefs/2026-07-20
```

Rendering is **non-fatal** in both the workflow (`continue-on-error`) and
`run_daily.sh`: a headless-browser hiccup never blocks the brief itself from
publishing. Set `RENDER_PICTURES=0` to skip it in `run_daily.sh`.

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
