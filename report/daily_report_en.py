# -*- coding: utf-8 -*-
"""
daily_report_en.py — the daily ENGLISH post (working-paper figures).
====================================================================

    python daily_report_en.py

Steps (each fails loud and stops the run):
  1. pull_supabase   : live uybor_listings_v2 -> data/uybor_listings_v2.csv
  2. pipeline        : merge v1+v2, clean, compute build/metrics.json + pickles
  3. figures_en      : render the English figures (figures_en/)
  4. send_telegram_en: post exactly the paper's 12 figures to the channel

Scheduled at 07:00 Asia/Tashkent by report-en.yml (the Uzbek set posts
separately at 06:00 via daily_report.py). Run from the report/ directory.
"""
import sys

import pull_supabase
import pipeline
import figures_en
import send_telegram_en


def main():
    rc = pull_supabase.main()
    if rc:
        return rc
    pipeline.main()
    figures_en.main()
    return send_telegram_en.main()


if __name__ == "__main__":
    sys.exit(main())
