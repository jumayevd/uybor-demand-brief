# -*- coding: utf-8 -*-
"""
pull_supabase.py — dump the live uybor_listings_v2 table to data/uybor_listings_v2.csv
=======================================================================================

The report pipeline (build.py) reads CSVs. This step refreshes the v2 CSV from
Supabase so every run uses live data. The v1 20-July backfill is a frozen file
(data/uybor_listings_v1_rows.csv) committed to the repo — it never changes — so
only v2 is pulled here. config.CSV_INPUTS merges the two.

Env:
  SUPABASE_DB_URL   Postgres connection string (never hardcode / never logged)
  UYBOR_TABLE       source table, default uybor_listings_v2

Fail-loud: a bad connection, zero rows, or a missing column aborts with a clear
message and leaves the previous CSV untouched (atomic temp-file + replace).
"""
import os
import re
import sys
import tempfile

import pandas as pd

DB_URL_ENV = "SUPABASE_DB_URL"
TABLE_ENV = "UYBOR_TABLE"
DEFAULT_TABLE = "uybor_listings_v2"
OUT = os.path.join(os.path.dirname(__file__), "data", "uybor_listings_v2.csv")

# columns the pipeline reads (see report/README.md schema)
COLUMNS = [
    "listing_id", "snapshot_date", "category", "city", "district",
    "price_usd", "area_m2", "rooms", "is_new_building", "renovation",
    "latitude", "longitude", "posted_at", "views", "clicks", "favorites",
]


def main(argv=None):
    db_url = os.environ.get(DB_URL_ENV)
    if not db_url:
        print(f"PULL FAILED: ${DB_URL_ENV} is not set", file=sys.stderr)
        return 1
    table = os.environ.get(TABLE_ENV, DEFAULT_TABLE)
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
        print(f"PULL FAILED: invalid table name {table!r}", file=sys.stderr)
        return 1

    from sqlalchemy import create_engine, text
    query = f'SELECT {", ".join(COLUMNS)} FROM {table}'
    engine = create_engine(db_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
    except Exception as exc:  # never echo db_url (it embeds the password)
        print(f"PULL FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    if df.empty:
        print(f"PULL FAILED: {table} returned 0 rows", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(OUT), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            df.to_csv(fh, index=False)
        os.replace(tmp, OUT)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

    print(f"[pull] {table}: {len(df):,} rows, "
          f"{df['listing_id'].nunique():,} listings -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
