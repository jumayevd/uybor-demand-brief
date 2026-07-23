"""
config.py — the ONLY file you edit for a daily run.
=====================================================

Point CSV_INPUTS at the scrape files for the window you want to report on, then
run:  python build.py

Each entry is (csv_path, snapshot_date_or_None):
  - If the CSV already has a `snapshot_date` column, pass None and it is used.
  - If it does NOT (a one-off snapshot export), pass the date string 'YYYY-MM-DD'
    and every row in that file is stamped with it.

For the automated daily job, the simplest pattern is a single rolling CSV that
already carries `snapshot_date` for every day scraped so far:

    CSV_INPUTS = [("data/uybor_panel.csv", None)]

The example below reproduces the working-paper window (24 June – 21 July 2026),
where the main panel carried dates and one extra export was the 20 July snapshot.
"""

# --- daily-run inputs -------------------------------------------------------
CSV_INPUTS = [
    ("data/uybor_listings_v2.csv",       None),          # v2: pulled fresh from Supabase each run (has snapshot_date)
    ("data/uybor_listings_v1_rows.csv",  "2026-07-20"),  # v1: frozen 20-Jul backfill, stamped
]

# --- output locations -------------------------------------------------------
BUILD_DIR = "build"       # L.pkl, P.pkl, metrics.json
FIG_DIR = "figures"       # all fig_*.pdf

# --- segment definition (do not change unless the market definition changes) -
CITY = "Ташкент"
CATEGORY = "Квартира"     # apartments only

# plausibility bounds: (min, max) inclusive
BOUNDS = dict(
    price_usd=(3_000, 5_000_000),
    area_m2=(15, 500),
    rooms=(1, 8),
    ppsm=(200, 6_000),          # price per square meter, $/m^2
)

# platform listing term used in the exit decomposition (renewal wall = [lo, hi])
LISTING_TERM_DAYS = (42, 44)

# price bands for the supply-vs-demand figure
PRICE_BANDS = [0, 30_000, 50_000, 75_000, 100_000, 150_000, 250_000, 1e9]
PRICE_BAND_LABELS = ["<30k", "30-50k", "50-75k", "75-100k",
                     "100-150k", "150-250k", "250k+"]

# Russian district name -> English label (12 Tashkent city districts)
DISTRICT_MAP = {
    "Шайхантахурский район": "Shaykhantakhur",
    "Юнусабадский район":    "Yunusabad",
    "Янгихаётский район":    "Yangihayot",
    "Бектемирский район":    "Bektemir",
    "Сергелийский район":    "Sergeli",
    "Алмазарский район":     "Almazar",
    "Мирзо-Улугбекский район": "Mirzo-Ulugbek",
    "Чиланзарский район":    "Chilanzar",
    "Яккасарайский район":   "Yakkasaray",
    "Учтепинский район":     "Uchtepa",
    "Мирабадский район":     "Mirabad",
    "Яшнабадский район":     "Yashnabad",
}
